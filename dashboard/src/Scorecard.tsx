import React, { useState, useEffect, useMemo, useCallback } from 'react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import './Scorecard.css';

// Types
interface ESHit<T> {
  _source: T;
  _id: string;
}

interface ESResponse<T> {
  hits: {
    hits: ESHit<T>[];
    total: { value: number };
  };
}

interface ScorecardMetrics {
  totalSessions: number;
  avgSessionDuration: number;
  totalCommands: number;
  uniqueUsers: number;
  avgEngagementScore: number;
  topSkills: Array<{ skill: string; progress: number }>;
  riskStudents: number;
  activeServers: number;
  avgCpuUsage: number;
  avgMemoryUsage: number;
  totalAlerts: number;
  dangerousCommands: number;
  totalApps: number;
  avgDailyActivity: number;
}

// Custom hook for ES queries with date filtering
function useESQuery<T>(
  baseUrl: string,
  index: string,
  query: string,
  startDate?: Date,
  endDate?: Date
) {
  const [data, setData] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const gte = startDate
          ? startDate.toISOString()
          : new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
        const lte = endDate ? endDate.toISOString() : new Date().toISOString();

        const response = await fetch(`${baseUrl}/${index}/_search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: {
              bool: {
                must: [
                  { query_string: { query } },
                  {
                    range: {
                      timestamp: {
                        gte: gte,
                        lte: lte,
                      },
                    },
                  },
                ],
              },
            },
            sort: [{ timestamp: { order: 'desc' } }],
            size: 10000,
          }),
        });

        if (response.ok) {
          const result: ESResponse<T> = await response.json();
          setData(result.hits.hits.map((h) => h._source));
        } else {
          setData([]);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
        setData([]);
      } finally {
        setIsLoading(false);
      }
    };

    const timeoutId = setTimeout(fetchData, 300);
    return () => clearTimeout(timeoutId);
  }, [baseUrl, index, query, startDate, endDate]);

  return { data, isLoading };
}

export default function Scorecard() {
  const baseUrl = '/es';
  const [indexPattern, setIndexPattern] = useState<string>('lab_monitoring');
  const [availableIndices, setAvailableIndices] = useState<string[]>([]);
  const [loadingIndices, setLoadingIndices] = useState<boolean>(false);

  const formatDateForInput = useCallback((date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }, []);

  const [dateRange, setDateRange] = useState<{ start: string; end: string }>(
    () => {
      const now = new Date();
      const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      return {
        start: formatDateForInput(sevenDaysAgo),
        end: formatDateForInput(now),
      };
    }
  );

  // Fetch available indices
  useEffect(() => {
    const fetchIndices = async () => {
      setLoadingIndices(true);
      try {
        const response = await fetch(`${baseUrl}/_cat/indices/lab_mon*?format=json`);
        if (response.ok) {
          const indices = await response.json();
          const indexNames = indices
            .map((idx: any) => idx.index)
            .filter((name: string) => name.startsWith('lab_mon'));
          setAvailableIndices(indexNames.length > 0 ? indexNames : ['lab_monitoring']);
        }
      } catch (error) {
        console.error('Error fetching indices:', error);
        setAvailableIndices(['lab_monitoring']);
      } finally {
        setLoadingIndices(false);
      }
    };
    fetchIndices();
  }, [baseUrl]);

  const startDate = useMemo(() => {
    const dateStr = dateRange.start + ':00';
    return new Date(dateStr);
  }, [dateRange.start]);

  const endDate = useMemo(() => {
    const dateStr = dateRange.end + ':00';
    return new Date(dateStr);
  }, [dateRange.end]);

  // Fetch data for scorecard metrics
  const engagementSessions = useESQuery<any>(
    baseUrl,
    indexPattern,
    'event_type:engagement_session',
    startDate,
    endDate
  );
  const engagementMetrics = useESQuery<any>(
    baseUrl,
    indexPattern,
    'event_type:engagement_metrics',
    startDate,
    endDate
  );
  const commands = useESQuery<any>(
    baseUrl,
    indexPattern,
    'event_type:command_monitoring',
    startDate,
    endDate
  );
  const learningProgress = useESQuery<any>(
    baseUrl,
    indexPattern,
    'event_type:learning_progress',
    startDate,
    endDate
  );
  const dropoutRisk = useESQuery<any>(
    baseUrl,
    indexPattern,
    'event_type:dropout_risk_assessment',
    startDate,
    endDate
  );
  const performance = useESQuery<any>(
    baseUrl,
    indexPattern,
    'event_type:performance_metrics',
    startDate,
    endDate
  );
  const appUsage = useESQuery<any>(
    baseUrl,
    indexPattern,
    'event_type:app_usage_stats',
    startDate,
    endDate
  );
  const dailyActivity = useESQuery<any>(
    baseUrl,
    indexPattern,
    'event_type:daily_activity',
    startDate,
    endDate
  );

  const isLoading =
    engagementSessions.isLoading ||
    engagementMetrics.isLoading ||
    commands.isLoading ||
    learningProgress.isLoading ||
    dropoutRisk.isLoading ||
    performance.isLoading ||
    appUsage.isLoading ||
    dailyActivity.isLoading;

  // Calculate scorecard metrics
  const metrics: ScorecardMetrics = useMemo(() => {
    // Session metrics
    const sessions = engagementSessions.data;
    const totalSessions = sessions.length;
    const avgSessionDuration =
      sessions.length > 0
        ? sessions.reduce((sum, s) => {
            const duration =
              s.data?.duration_minutes ||
              s.data?.duration ||
              s.data?.session_duration ||
              0;
            return sum + duration;
          }, 0) / sessions.length
        : 0;

    // Command metrics
    const commandData = commands.data;
    let totalCommands = 0;
    let dangerousCommands = 0;
    commandData.forEach((cmd) => {
      const data = cmd.data || {};
      totalCommands += data.total_commands || 0;
      if (data.recent_alerts) {
        dangerousCommands += data.recent_alerts.filter(
          (a: any) => a.risk_level === 'high' || a.risk_level === 'critical'
        ).length;
      }
    });

    // User metrics
    const uniqueUsersSet = new Set();
    sessions.forEach((s) => {
      if (s.data?.user_id) uniqueUsersSet.add(s.data.user_id);
    });
    engagementMetrics.data.forEach((m) => {
      if (m.data?.user_id) uniqueUsersSet.add(m.data.user_id);
    });
    const uniqueUsers = uniqueUsersSet.size;

    // Engagement score
    const engagementScores = engagementMetrics.data
      .map((m) => m.data?.engagement_score || m.data?.score || 0)
      .filter((s) => s > 0);
    const avgEngagementScore =
      engagementScores.length > 0
        ? engagementScores.reduce((a, b) => a + b, 0) / engagementScores.length
        : 0;

    // Top skills
    const skillMap: Record<string, number[]> = {};
    learningProgress.data.forEach((lp) => {
      const skill = lp.data?.skill;
      const progress = lp.data?.progress_percent || 0;
      if (skill && progress > 0) {
        if (!skillMap[skill]) skillMap[skill] = [];
        skillMap[skill].push(progress);
      }
    });
    const topSkills = Object.entries(skillMap)
      .map(([skill, progresses]) => ({
        skill,
        progress: progresses.reduce((a, b) => a + b, 0) / progresses.length,
      }))
      .sort((a, b) => b.progress - a.progress)
      .slice(0, 5);

    // Risk students
    const riskStudents = dropoutRisk.data.filter(
      (d) => (d.data?.risk_score || 0) > 0.7
    ).length;

    // Server metrics
    const serverSet = new Set();
    performance.data.forEach((p) => {
      if (p.server_id) serverSet.add(p.server_id);
    });
    const activeServers = serverSet.size;

    // CPU and Memory
    const cpuValues = performance.data
      .map((p) => p.data?.cpu?.utilization_percent || 0)
      .filter((v) => v > 0);
    const avgCpuUsage =
      cpuValues.length > 0
        ? cpuValues.reduce((a, b) => a + b, 0) / cpuValues.length
        : 0;

    const memValues = performance.data
      .map((p) => p.data?.memory?.ram_percent || 0)
      .filter((v) => v > 0);
    const avgMemoryUsage =
      memValues.length > 0
        ? memValues.reduce((a, b) => a + b, 0) / memValues.length
        : 0;

    // Alerts
    let totalAlerts = 0;
    commandData.forEach((cmd) => {
      const data = cmd.data || {};
      totalAlerts += (data.recent_alerts || []).length;
    });

    // Apps
    const appSet = new Set();
    appUsage.data.forEach((app) => {
      if (app.data?.app_name) appSet.add(app.data.app_name);
    });
    const totalApps = appSet.size;

    // Daily activity
    const activityHours = dailyActivity.data
      .map((d) => d.data?.total_hours || 0)
      .filter((h) => h > 0);
    const avgDailyActivity =
      activityHours.length > 0
        ? activityHours.reduce((a, b) => a + b, 0) / activityHours.length
        : 0;

    return {
      totalSessions,
      avgSessionDuration,
      totalCommands,
      uniqueUsers,
      avgEngagementScore,
      topSkills,
      riskStudents,
      activeServers,
      avgCpuUsage,
      avgMemoryUsage,
      totalAlerts,
      dangerousCommands,
      totalApps,
      avgDailyActivity,
    };
  }, [
    engagementSessions.data,
    engagementMetrics.data,
    commands.data,
    learningProgress.data,
    dropoutRisk.data,
    performance.data,
    appUsage.data,
    dailyActivity.data,
  ]);

  // Download report as PDF
  const downloadReport = useCallback(async () => {
    const scorecardElement = document.getElementById('scorecard-content');
    if (!scorecardElement) return;

    try {
      const canvas = await html2canvas(scorecardElement, {
        scale: 2,
        logging: false,
        useCORS: true,
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pdfWidth - 20;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      let heightLeft = imgHeight;
      let position = 10;

      pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
      heightLeft -= pdfHeight;

      while (heightLeft > 0) {
        position = heightLeft - imgHeight + 10;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
        heightLeft -= pdfHeight;
      }

      const fileName = `scorecard_${indexPattern}_${new Date().toISOString().split('T')[0]}.pdf`;
      pdf.save(fileName);
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('Failed to generate PDF report');
    }
  }, [indexPattern]);

  // Download report as JSON
  const downloadJSON = useCallback(() => {
    const reportData = {
      generated_at: new Date().toISOString(),
      index_pattern: indexPattern,
      date_range: {
        start: dateRange.start,
        end: dateRange.end,
      },
      metrics,
      raw_data: {
        engagement_sessions: engagementSessions.data,
        engagement_metrics: engagementMetrics.data,
        commands: commands.data,
        learning_progress: learningProgress.data,
        dropout_risk: dropoutRisk.data,
        performance: performance.data,
        app_usage: appUsage.data,
        daily_activity: dailyActivity.data,
      },
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scorecard_${indexPattern}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [indexPattern, dateRange, metrics, engagementSessions.data, engagementMetrics.data, commands.data, learningProgress.data, dropoutRisk.data, performance.data, appUsage.data, dailyActivity.data]);

  return (
    <div className="scorecard-container">
      <div className="scorecard-header">
        <h1>📊 Lab Monitoring Scorecard</h1>
        <p className="scorecard-subtitle">Comprehensive metrics and insights</p>
      </div>

      {/* Filters */}
      <div className="scorecard-filters">
        <div className="filter-group">
          <label>Index Pattern:</label>
          <select
            value={indexPattern}
            onChange={(e) => setIndexPattern(e.target.value)}
            disabled={loadingIndices}
          >
            {availableIndices.map((idx) => (
              <option key={idx} value={idx}>
                {idx}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Start Date:</label>
          <input
            type="datetime-local"
            value={dateRange.start}
            onChange={(e) =>
              setDateRange({ ...dateRange, start: e.target.value })
            }
          />
        </div>

        <div className="filter-group">
          <label>End Date:</label>
          <input
            type="datetime-local"
            value={dateRange.end}
            onChange={(e) =>
              setDateRange({ ...dateRange, end: e.target.value })
            }
          />
        </div>

        <div className="filter-actions">
          <button onClick={downloadReport} className="btn-download">
            📄 Download PDF
          </button>
          <button onClick={downloadJSON} className="btn-download">
            💾 Download JSON
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="scorecard-loading">
          <div className="spinner"></div>
          <p>Loading metrics...</p>
        </div>
      ) : (
        <div id="scorecard-content" className="scorecard-content">
          {/* Summary Cards */}
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-icon">👥</div>
              <div className="metric-value">{metrics.uniqueUsers}</div>
              <div className="metric-label">Unique Users</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">🎯</div>
              <div className="metric-value">{metrics.totalSessions}</div>
              <div className="metric-label">Total Sessions</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">⏱️</div>
              <div className="metric-value">
                {metrics.avgSessionDuration.toFixed(1)} min
              </div>
              <div className="metric-label">Avg Session Duration</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">💻</div>
              <div className="metric-value">{metrics.totalCommands}</div>
              <div className="metric-label">Total Commands</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">📊</div>
              <div className="metric-value">
                {metrics.avgEngagementScore.toFixed(1)}
              </div>
              <div className="metric-label">Avg Engagement Score</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">⚠️</div>
              <div className="metric-value">{metrics.riskStudents}</div>
              <div className="metric-label">At-Risk Students</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">🖥️</div>
              <div className="metric-value">{metrics.activeServers}</div>
              <div className="metric-label">Active Servers</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">📱</div>
              <div className="metric-value">{metrics.totalApps}</div>
              <div className="metric-label">Unique Applications</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">⚙️</div>
              <div className="metric-value">
                {metrics.avgCpuUsage.toFixed(1)}%
              </div>
              <div className="metric-label">Avg CPU Usage</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">🧠</div>
              <div className="metric-value">
                {metrics.avgMemoryUsage.toFixed(1)}%
              </div>
              <div className="metric-label">Avg Memory Usage</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">🔔</div>
              <div className="metric-value">{metrics.totalAlerts}</div>
              <div className="metric-label">Total Alerts</div>
            </div>

            <div className="metric-card danger">
              <div className="metric-icon">🚨</div>
              <div className="metric-value">{metrics.dangerousCommands}</div>
              <div className="metric-label">Dangerous Commands</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">📈</div>
              <div className="metric-value">
                {metrics.avgDailyActivity.toFixed(1)} hrs
              </div>
              <div className="metric-label">Avg Daily Activity</div>
            </div>
          </div>

          {/* Top Skills Section */}
          {metrics.topSkills.length > 0 && (
            <div className="scorecard-section">
              <h2>🏆 Top Skills by Progress</h2>
              <div className="skills-list">
                {metrics.topSkills.map((skill, idx) => (
                  <div key={idx} className="skill-item">
                    <div className="skill-name">
                      {idx + 1}. {skill.skill}
                    </div>
                    <div className="skill-progress-container">
                      <div
                        className="skill-progress-bar"
                        style={{ width: `${skill.progress}%` }}
                      >
                        <span className="skill-progress-text">
                          {skill.progress.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Report Metadata */}
          <div className="scorecard-footer">
            <p>
              <strong>Report Generated:</strong>{' '}
              {new Date().toLocaleString()}
            </p>
            <p>
              <strong>Index Pattern:</strong> {indexPattern}
            </p>
            <p>
              <strong>Date Range:</strong> {dateRange.start} to {dateRange.end}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
