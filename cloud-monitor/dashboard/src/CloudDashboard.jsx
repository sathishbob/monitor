import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './CloudDashboard.css';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const CloudDashboard = () => {
  const [metrics, setMetrics] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState('all');
  const [selectedService, setSelectedService] = useState('all');
  const [timeRange, setTimeRange] = useState('1h');
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Elasticsearch endpoint
  const ES_URL = 'http://localhost:9200/cloud-usage-metrics/_search';

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [selectedProvider, selectedService, timeRange]);

  const fetchMetrics = async () => {
    try {
      const timeRanges = {
        '1h': 'now-1h',
        '6h': 'now-6h',
        '24h': 'now-24h',
        '7d': 'now-7d',
        '30d': 'now-30d'
      };

      const query = {
        query: {
          bool: {
            must: [
              {
                range: {
                  timestamp: {
                    gte: timeRanges[timeRange],
                    lte: 'now'
                  }
                }
              }
            ],
            filter: []
          }
        },
        size: 1000,
        sort: [{ timestamp: { order: 'desc' } }]
      };

      if (selectedProvider !== 'all') {
        query.query.bool.filter.push({
          term: { cloud_provider: selectedProvider }
        });
      }

      if (selectedService !== 'all') {
        query.query.bool.filter.push({
          term: { service: selectedService }
        });
      }

      const response = await axios.post(ES_URL, query);
      const data = response.data.hits.hits.map(hit => hit._source);
      setMetrics(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      setLoading(false);
    }
  };

  // Calculate statistics
  const getProviderDistribution = () => {
    const distribution = {};
    metrics.forEach(m => {
      distribution[m.cloud_provider] = (distribution[m.cloud_provider] || 0) + 1;
    });
    return Object.entries(distribution).map(([name, value]) => ({ name, value }));
  };

  const getServiceDistribution = () => {
    const distribution = {};
    metrics.forEach(m => {
      distribution[m.service] = (distribution[m.service] || 0) + 1;
    });
    return Object.entries(distribution).map(([name, value]) => ({ name, value }));
  };

  const getCPUTrend = () => {
    return metrics
      .filter(m => m.cpu_utilization !== undefined)
      .slice(0, 50)
      .reverse()
      .map((m, i) => ({
        time: new Date(m.timestamp).toLocaleTimeString(),
        cpu: m.cpu_utilization,
        resource: m.resource_id
      }));
  };

  const getMemoryTrend = () => {
    return metrics
      .filter(m => m.memory_utilization !== undefined)
      .slice(0, 50)
      .reverse()
      .map((m, i) => ({
        time: new Date(m.timestamp).toLocaleTimeString(),
        memory: m.memory_utilization,
        resource: m.resource_id
      }));
  };

  const getTopResourcesByUsage = () => {
    const resourceUsage = {};
    metrics.forEach(m => {
      if (m.cpu_utilization) {
        if (!resourceUsage[m.resource_id]) {
          resourceUsage[m.resource_id] = {
            id: m.resource_id,
            service: m.service,
            provider: m.cloud_provider,
            cpu: 0,
            count: 0
          };
        }
        resourceUsage[m.resource_id].cpu += m.cpu_utilization;
        resourceUsage[m.resource_id].count += 1;
      }
    });

    return Object.values(resourceUsage)
      .map(r => ({ ...r, avgCPU: r.cpu / r.count }))
      .sort((a, b) => b.avgCPU - a.avgCPU)
      .slice(0, 10);
  };

  const getAlerts = () => {
    const alertThresholds = {
      cpu: 80,
      memory: 85,
      disk: 90
    };

    const currentAlerts = metrics.filter(m => {
      return (
        (m.cpu_utilization && m.cpu_utilization > alertThresholds.cpu) ||
        (m.memory_utilization && m.memory_utilization > alertThresholds.memory) ||
        (m.disk_utilization && m.disk_utilization > alertThresholds.disk)
      );
    });

    return currentAlerts.slice(0, 20);
  };

  const providers = ['all', ...new Set(metrics.map(m => m.cloud_provider))];
  const services = ['all', ...new Set(metrics.map(m => m.service))];

  return (
    <div className="cloud-dashboard">
      <header className="dashboard-header">
        <h1>☁️ Multi-Cloud Monitoring Dashboard</h1>
        <div className="header-controls">
          <select value={selectedProvider} onChange={(e) => setSelectedProvider(e.target.value)}>
            {providers.map(p => (
              <option key={p} value={p}>{p.toUpperCase()}</option>
            ))}
          </select>

          <select value={selectedService} onChange={(e) => setSelectedService(e.target.value)}>
            <option value="all">All Services</option>
            {services.filter(s => s !== 'all').map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>

          <button onClick={fetchMetrics} className="refresh-btn">🔄 Refresh</button>
        </div>
      </header>

      {loading ? (
        <div className="loading">Loading metrics...</div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="summary-cards">
            <div className="card">
              <h3>Total Resources</h3>
              <div className="card-value">{metrics.length}</div>
            </div>
            <div className="card">
              <h3>Cloud Providers</h3>
              <div className="card-value">{new Set(metrics.map(m => m.cloud_provider)).size}</div>
            </div>
            <div className="card">
              <h3>Services Monitored</h3>
              <div className="card-value">{new Set(metrics.map(m => m.service)).size}</div>
            </div>
            <div className="card alert-card">
              <h3>Active Alerts</h3>
              <div className="card-value">{getAlerts().length}</div>
            </div>
          </div>

          {/* Alerts Section */}
          {getAlerts().length > 0 && (
            <div className="alerts-section">
              <h2>🚨 Active Alerts</h2>
              <div className="alerts-list">
                {getAlerts().map((alert, idx) => (
                  <div key={idx} className="alert-item">
                    <span className="alert-severity">⚠️ WARNING</span>
                    <span className="alert-provider">{alert.cloud_provider.toUpperCase()}</span>
                    <span className="alert-resource">{alert.resource_id}</span>
                    <span className="alert-message">
                      {alert.cpu_utilization > 80 && `CPU: ${alert.cpu_utilization.toFixed(1)}%`}
                      {alert.memory_utilization > 85 && `Memory: ${alert.memory_utilization.toFixed(1)}%`}
                    </span>
                    <span className="alert-time">{new Date(alert.timestamp).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Charts Grid */}
          <div className="charts-grid">
            {/* Provider Distribution */}
            <div className="chart-container">
              <h2>Resources by Provider</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={getProviderDistribution()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {getProviderDistribution().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Service Distribution */}
            <div className="chart-container">
              <h2>Resources by Service</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={getServiceDistribution().slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* CPU Trend */}
            <div className="chart-container full-width">
              <h2>CPU Utilization Trend</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={getCPUTrend()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="cpu" stroke="#8884d8" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Memory Trend */}
            <div className="chart-container full-width">
              <h2>Memory Utilization Trend</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={getMemoryTrend()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="memory" stroke="#82ca9d" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top Resources Table */}
          <div className="table-container">
            <h2>Top Resources by CPU Usage</h2>
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Resource ID</th>
                  <th>Provider</th>
                  <th>Service</th>
                  <th>Avg CPU %</th>
                </tr>
              </thead>
              <tbody>
                {getTopResourcesByUsage().map((resource, idx) => (
                  <tr key={idx}>
                    <td>{resource.id}</td>
                    <td>{resource.provider.toUpperCase()}</td>
                    <td>{resource.service}</td>
                    <td className={resource.avgCPU > 80 ? 'high-usage' : ''}>
                      {resource.avgCPU.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

export default CloudDashboard;
