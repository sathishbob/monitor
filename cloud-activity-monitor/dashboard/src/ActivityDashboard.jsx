import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './ActivityDashboard.css';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const ActivityDashboard = () => {
    const [activities, setActivities] = useState([]);
    const [userSummaries, setUserSummaries] = useState([]);
    const [anomalies, setAnomalies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedTab, setSelectedTab] = useState('overview');
    const [selectedUser, setSelectedUser] = useState(null);
    const [timeRange, setTimeRange] = useState('1h');

    const ES_HOST = 'http://localhost:9200';
    const INDEX_NAME = 'cloud-user-activities';

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, [timeRange]);

    const fetchData = async () => {
        try {
            setLoading(true);

            // Fetch user activities
            const activitiesResponse = await axios.post(`${ES_HOST}/${INDEX_NAME}/_search`, {
                query: {
                    bool: {
                        filter: [
                            {
                                range: {
                                    timestamp: {
                                        gte: `now-${timeRange}`
                                    }
                                }
                            },
                            {
                                term: {
                                    type: 'user_activity'
                                }
                            }
                        ]
                    }
                },
                size: 1000,
                sort: [{ timestamp: 'desc' }]
            });

            // Fetch user summaries
            const summariesResponse = await axios.post(`${ES_HOST}/${INDEX_NAME}/_search`, {
                query: {
                    bool: {
                        filter: [
                            {
                                range: {
                                    timestamp: {
                                        gte: `now-${timeRange}`
                                    }
                                }
                            },
                            {
                                term: {
                                    type: 'user_summary'
                                }
                            }
                        ]
                    }
                },
                size: 100,
                sort: [{ timestamp: 'desc' }]
            });

            // Fetch anomalies
            const anomaliesResponse = await axios.post(`${ES_HOST}/${INDEX_NAME}/_search`, {
                query: {
                    bool: {
                        filter: [
                            {
                                range: {
                                    timestamp: {
                                        gte: `now-${timeRange}`
                                    }
                                }
                            },
                            {
                                term: {
                                    type: 'anomaly'
                                }
                            }
                        ]
                    }
                },
                size: 100,
                sort: [{ timestamp: 'desc' }]
            });

            setActivities(activitiesResponse.data.hits.hits.map(hit => hit._source));
            setUserSummaries(summariesResponse.data.hits.hits.map(hit => hit._source));
            setAnomalies(anomaliesResponse.data.hits.hits.map(hit => hit._source));

            setLoading(false);
        } catch (error) {
            console.error('Error fetching data:', error);
            setLoading(false);
        }
    };

    // Calculate overview statistics
    const getOverviewStats = () => {
        const totalUsers = new Set(activities.map(a => a.user_identity.user_name)).size;
        const totalActions = activities.length;
        const successRate = activities.filter(a => a.success).length / totalActions * 100 || 0;
        const totalAnomalies = anomalies.length;

        return { totalUsers, totalActions, successRate, totalAnomalies };
    };

    // Get top users by activity
    const getTopUsers = () => {
        const userCounts = {};
        activities.forEach(a => {
            const user = a.user_identity.user_name;
            userCounts[user] = (userCounts[user] || 0) + 1;
        });

        return Object.entries(userCounts)
            .map(([name, count]) => ({ name, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 10);
    };

    // Get service usage distribution
    const getServiceDistribution = () => {
        const serviceCounts = {};
        activities.forEach(a => {
            serviceCounts[a.service] = (serviceCounts[a.service] || 0) + 1;
        });

        return Object.entries(serviceCounts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 8);
    };

    // Get action type distribution
    const getActionDistribution = () => {
        const actionCounts = {};
        activities.forEach(a => {
            const category = a.action_category || 'Other';
            actionCounts[category] = (actionCounts[category] || 0) + 1;
        });

        return Object.entries(actionCounts)
            .map(([name, value]) => ({ name, value }));
    };

    // Get cloud provider distribution
    const getCloudDistribution = () => {
        const cloudCounts = {};
        activities.forEach(a => {
            cloudCounts[a.cloud_provider.toUpperCase()] = (cloudCounts[a.cloud_provider.toUpperCase()] || 0) + 1;
        });

        return Object.entries(cloudCounts)
            .map(([name, value]) => ({ name, value }));
    };

    // Get activity timeline
    const getActivityTimeline = () => {
        const timeline = {};
        activities.forEach(a => {
            const hour = new Date(a.timestamp).toISOString().slice(0, 13) + ':00';
            timeline[hour] = (timeline[hour] || 0) + 1;
        });

        return Object.entries(timeline)
            .map(([time, count]) => ({ time: time.slice(11, 16), count }))
            .sort((a, b) => a.time.localeCompare(b.time));
    };

    const stats = getOverviewStats();

    return (
        <div className="activity-dashboard">
            <header className="dashboard-header">
                <h1>☁️ Cloud User Activity Monitor</h1>
                <div className="time-range-selector">
                    <button onClick={() => setTimeRange('1h')} className={timeRange === '1h' ? 'active' : ''}>1h</button>
                    <button onClick={() => setTimeRange('6h')} className={timeRange === '6h' ? 'active' : ''}>6h</button>
                    <button onClick={() => setTimeRange('24h')} className={timeRange === '24h' ? 'active' : ''}>24h</button>
                    <button onClick={() => setTimeRange('7d')} className={timeRange === '7d' ? 'active' : ''}>7d</button>
                </div>
            </header>

            <div className="tabs">
                <button onClick={() => setSelectedTab('overview')} className={selectedTab === 'overview' ? 'active' : ''}>
                    Overview
                </button>
                <button onClick={() => setSelectedTab('users')} className={selectedTab === 'users' ? 'active' : ''}>
                    User Activity
                </button>
                <button onClick={() => setSelectedTab('services')} className={selectedTab === 'services' ? 'active' : ''}>
                    Services
                </button>
                <button onClick={() => setSelectedTab('anomalies')} className={selectedTab === 'anomalies' ? 'active' : ''}>
                    Anomalies {anomalies.length > 0 && <span className="badge">{anomalies.length}</span>}
                </button>
                <button onClick={() => setSelectedTab('timeline')} className={selectedTab === 'timeline' ? 'active' : ''}>
                    Timeline
                </button>
            </div>

            {loading ? (
                <div className="loading">Loading activity data...</div>
            ) : (
                <>
                    {selectedTab === 'overview' && (
                        <div className="overview-tab">
                            <div className="stats-grid">
                                <div className="stat-card">
                                    <h3>Total Users</h3>
                                    <div className="stat-value">{stats.totalUsers}</div>
                                </div>
                                <div className="stat-card">
                                    <h3>Total Actions</h3>
                                    <div className="stat-value">{stats.totalActions}</div>
                                </div>
                                <div className="stat-card">
                                    <h3>Success Rate</h3>
                                    <div className="stat-value">{stats.successRate.toFixed(1)}%</div>
                                </div>
                                <div className="stat-card alert">
                                    <h3>Anomalies</h3>
                                    <div className="stat-value">{stats.totalAnomalies}</div>
                                </div>
                            </div>

                            <div className="charts-grid">
                                <div className="chart-card">
                                    <h3>Top 10 Active Users</h3>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <BarChart data={getTopUsers()}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                                            <YAxis />
                                            <Tooltip />
                                            <Bar dataKey="count" fill="#8884d8" />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="chart-card">
                                    <h3>Cloud Provider Distribution</h3>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <PieChart>
                                            <Pie
                                                data={getCloudDistribution()}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={({ name, value }) => `${name}: ${value}`}
                                                outerRadius={80}
                                                fill="#8884d8"
                                                dataKey="value"
                                            >
                                                {getCloudDistribution().map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="chart-card">
                                    <h3>Action Types</h3>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <PieChart>
                                            <Pie
                                                data={getActionDistribution()}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={({ name, value }) => `${name}: ${value}`}
                                                outerRadius={80}
                                                fill="#82ca9d"
                                                dataKey="value"
                                            >
                                                {getActionDistribution().map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="chart-card">
                                    <h3>Top Services</h3>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <BarChart data={getServiceDistribution()}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="name" />
                                            <YAxis />
                                            <Tooltip />
                                            <Bar dataKey="value" fill="#00C49F" />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>
                    )}

                    {selectedTab === 'users' && (
                        <div className="users-tab">
                            <h2>User Activity Summary</h2>
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>User</th>
                                        <th>Cloud</th>
                                        <th>Account</th>
                                        <th>Total Actions</th>
                                        <th>Success</th>
                                        <th>Failed</th>
                                        <th>Error Rate</th>
                                        <th>Services</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {userSummaries.map((summary, idx) => (
                                        <tr key={idx}>
                                            <td>{summary.user_name}</td>
                                            <td>{summary.cloud_provider.toUpperCase()}</td>
                                            <td>{summary.account}</td>
                                            <td>{summary.metrics.total_actions}</td>
                                            <td className="success">{summary.metrics.successful_actions}</td>
                                            <td className="error">{summary.metrics.failed_actions}</td>
                                            <td>{(summary.metrics.error_rate * 100).toFixed(1)}%</td>
                                            <td>{summary.metrics.service_count}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {selectedTab === 'services' && (
                        <div className="services-tab">
                            <h2>Service Usage</h2>
                            <div className="chart-card large">
                                <ResponsiveContainer width="100%" height={400}>
                                    <BarChart data={getServiceDistribution()}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <Bar dataKey="value" fill="#8884d8" name="Actions" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {selectedTab === 'anomalies' && (
                        <div className="anomalies-tab">
                            <h2>Detected Anomalies</h2>
                            {anomalies.length === 0 ? (
                                <div className="no-data">No anomalies detected</div>
                            ) : (
                                <div className="anomalies-list">
                                    {anomalies.map((anomaly, idx) => (
                                        <div key={idx} className={`anomaly-card ${anomaly.severity}`}>
                                            <div className="anomaly-header">
                                                <span className="anomaly-type">{anomaly.anomaly_type.replace(/_/g, ' ').toUpperCase()}</span>
                                                <span className={`severity-badge ${anomaly.severity}`}>{anomaly.severity}</span>
                                            </div>
                                            <p className="anomaly-description">{anomaly.description}</p>
                                            <div className="anomaly-details">
                                                <span>User: {anomaly.user_name}</span>
                                                <span>Cloud: {anomaly.cloud_provider.toUpperCase()}</span>
                                                <span>Account: {anomaly.account}</span>
                                                <span>Time: {new Date(anomaly.timestamp).toLocaleString()}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {selectedTab === 'timeline' && (
                        <div className="timeline-tab">
                            <h2>Activity Timeline</h2>
                            <div className="chart-card large">
                                <ResponsiveContainer width="100%" height={400}>
                                    <LineChart data={getActivityTimeline()}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="time" />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <Line type="monotone" dataKey="count" stroke="#8884d8" name="Actions" />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>

                            <h3>Recent Activities</h3>
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>User</th>
                                        <th>Cloud</th>
                                        <th>Service</th>
                                        <th>Action</th>
                                        <th>Status</th>
                                        <th>IP</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {activities.slice(0, 50).map((activity, idx) => (
                                        <tr key={idx}>
                                            <td>{new Date(activity.timestamp).toLocaleTimeString()}</td>
                                            <td>{activity.user_identity.user_name}</td>
                                            <td>{activity.cloud_provider.toUpperCase()}</td>
                                            <td>{activity.service}</td>
                                            <td>{activity.event_name}</td>
                                            <td className={activity.success ? 'success' : 'error'}>
                                                {activity.success ? '✓' : '✗'}
                                            </td>
                                            <td>{activity.source_ip}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default ActivityDashboard;
