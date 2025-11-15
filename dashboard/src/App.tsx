// Version: 2025-01-15-v3 - Fixed chart line hiding with conditional rendering
import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { LineChart, BarChart, PieChart, AreaChart, ComposedChart, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid, Cell, Line, Bar, Area, Pie } from 'recharts';
import './App.css';

// Types
interface ESHit<T> {
  _source: T;
  _id: string;
}

interface AlertRule {
  id: string;
  name: string;
  metric: string;
  condition: 'above' | 'below';
  threshold: number;
  enabled: boolean;
  tab: string;
}

interface AlertTrigger {
  ruleId: string;
  ruleName: string;
  value: number;
  threshold: number;
  timestamp: Date;
}

interface ESResponse<T> {
  hits: {
    hits: ESHit<T>[];
    total: { value: number };
  };
}

interface PerfDoc {
  timestamp: string;
  server_id: string;
  event_type: string;
  data: {
    timestamp: string;
    cpu: {
      utilization_percent: number;
      utilization_per_core: number[];
      frequency_mhz: number;
      frequency_min_mhz: number;
      frequency_max_mhz: number;
    };
    memory: {
      ram_total_gb: number;
      ram_available_gb: number;
      ram_used_gb: number;
      ram_percent: number;
      swap_total_gb: number;
      swap_used_gb: number;
      swap_percent: number;
    };
    disk: {
      partitions: any;
      io_read_bytes: number;
      io_write_bytes: number;
      io_read_count: number;
      io_write_count: number;
    };
    network: {
      bytes_sent: number;
      bytes_recv: number;
      packets_sent: number;
      packets_recv: number;
      interfaces: any;
    };
  };
}

interface CommandDoc {
  timestamp: string;
  command?: string;
  cmd?: string;
  command_text?: string;
  text?: string;
  name?: string;
  user_id?: string;
    dangerous?: boolean;
    duration_seconds?: number;
  risk_score?: number;
  data?: {
    recent_commands?: Array<{
      command?: string;
      cmd?: string;
      command_text?: string;
      text?: string;
      name?: string;
      risk_score?: number;
      dangerous?: boolean;
    }>;
    command_patterns?: Record<string, number>;
    total_commands?: number;
    active_alerts?: any[];
    security_metrics?: Record<string, any>;
    risk_distribution?: Record<string, number>;
  };
}

interface WindowUsageDoc {
  timestamp: string;
  data: {
    window_title: string;
    process_name: string;
    duration_seconds: number;
  };
}

interface UserAnalysisDoc {
  timestamp: string;
  data: {
    user_id: string;
    activity_score: number;
    engagement_level: string;
  };
}

interface CmdScoreDoc {
  timestamp: string;
  data: {
    command: string;
    score: number;
    category: string;
  };
}

interface EngagementSessionDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    session_id?: string;
    duration_minutes?: number;
    activity_count?: number;
    duration?: number;
    session_duration?: number;
    time_spent?: number;
    minutes?: number;
    activities?: number;
    commands_executed?: number;
    interactions?: number;
    count?: number;
    [key: string]: any; // Allow additional fields
  };
}

interface LearningProgressDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    skill: string;
    progress_percent: number;
    level: string;
  };
}

interface AppUsageDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    app_name: string;
    usage_minutes: number;
    category: string;
  };
}

interface DailyActivityDoc {
  timestamp: string;
  data: {
  date: string;
    total_hours: number;
    productivity_score: number;
  };
}

interface DropoutRiskDoc {
  timestamp: string;
  data: {
  user_id: string;
    risk_score: number;
    factors: string[];
  };
}

interface CrossServerDoc {
  timestamp: string;
  data: {
    server_id: string;
    comparison_metric: string;
    value: number;
  };
}

interface HeatmapDoc {
  timestamp: string;
  data: {
    hour: number;
    day: number;
    activity_count: number;
  };
}

interface TrendAnalysisDoc {
  timestamp: string;
  data: {
    metric: string;
    trend: string;
    confidence: number;
  };
}

interface PredictiveDoc {
  timestamp: string;
  data: {
    prediction_type: string;
    predicted_value: number;
    confidence: number;
  };
}

interface SecurityDoc {
  timestamp: string;
  data: {
  user_id: string;
  risk_score: number;
  risk_factors: string[];
    last_login_date: string;
    session_count: number;
};
}

interface ResourceDoc {
  timestamp: string;
  data: {
    user_id: string;
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
    network_bytes_sent: number;
    network_bytes_recv: number;
  };
}

// New monitoring module interfaces
interface FileSystemDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    files_created?: number;
    files_modified?: number;
    files_deleted?: number;
    total_lines?: number;
    git_commits?: number;
    languages?: Record<string, number>;
    project_type?: string;
    file_events?: any[];
  };
}

interface ErrorDebugDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    error_count?: number;
    error_type?: string;
    resolution_time_minutes?: number;
    debug_sessions?: number;
    stack_trace?: string;
    severity?: string;
  };
}

interface DevEnvironmentDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    ide_name?: string;
    usage_minutes?: number;
    plugins?: string[];
    configurations?: Record<string, any>;
    extensions_count?: number;
  };
}

interface BrowserActivityDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    site_url?: string;
    site_category?: string;
    is_educational?: boolean;
    duration_minutes?: number;
    page_title?: string;
  };
}

interface CodeQualityDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    file_path?: string;
    function_count?: number;
    comment_ratio?: number;
    test_coverage?: number;
    complexity_score?: number;
    quality_score?: number;
    lines_of_code?: number;
  };
}

interface PackageDependencyDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    package_name?: string;
    package_version?: string;
    install_time?: string;
    dependency_count?: number;
    has_conflicts?: boolean;
    virtual_env?: string;
  };
}

interface CollaborationDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    collaboration_type?: string;
    participants?: number;
    duration_minutes?: number;
    code_files_shared?: number;
  };
}

interface LearningPathDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    exercise_name?: string;
    assignment_name?: string;
    quiz_score?: number;
    milestone?: string;
    certificate?: string;
    completion_percent?: number;
  };
}

interface ResourceAccessDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    resource_type?: string;
    resource_name?: string;
    access_count?: number;
    data_transferred_mb?: number;
    response_time_ms?: number;
  };
}

interface TimeDistributionDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    activity_type?: string;
    duration_minutes?: number;
    context_switches?: number;
    focus_score?: number;
    productivity_score?: number;
  };
}

interface HardwareUtilizationDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    gpu_utilization?: number;
    gpu_memory_used_mb?: number;
    peripheral_type?: string;
    peripheral_usage_minutes?: number;
  };
}

interface NetworkBehaviorDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    transfer_type?: string;
    bytes_transferred?: number;
    repository?: string;
    bandwidth_mbps?: number;
    connection_count?: number;
  };
}

interface TerminalConsoleDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    command?: string;
    command_category?: string;
    execution_time_ms?: number;
    proficiency_score?: number;
    session_duration_minutes?: number;
  };
}

interface ProjectLifecycleDoc {
  timestamp: string;
  sourceIndex?: string;
  data: {
    project_name?: string;
    lifecycle_stage?: string;
    stage_duration_minutes?: number;
    success?: boolean;
    error_count?: number;
  };
}

// Custom hook for Elasticsearch queries with date filtering
function useESWithDateFilter<T>(baseUrl: string, index: string, query: string, startDate?: Date, endDate?: Date, availableIndices?: string[]) {
  const [data, setData] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Use provided dates or default to last 7 days
        // Convert local timezone dates to UTC for Elasticsearch queries
        const gte = startDate ? startDate.toISOString() : new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
        const lte = endDate ? endDate.toISOString() : new Date().toISOString();
        
        let allData: T[] = [];
        
        if (index === 'all' && availableIndices) {
          // Fetch data from all lab_mon* indices
          const labIndices = availableIndices.filter(idx => idx !== 'all' && idx.startsWith('lab_mon'));
          
          // If no lab indices found, fall back to single index logic
          if (labIndices.length === 0) {
            console.warn('No lab_mon* indices found, falling back to single index query');
            // Use the first available index as fallback
            const fallbackIndex = availableIndices.find(idx => idx !== 'all' && idx.startsWith('lab_mon')) || 'lab_monitoring';
            // Fall through to single index logic below with fallback index
          } else {
            for (const idx of labIndices) {
              try {
                // First check if index exists
                const indexExistsResponse = await fetch(`${baseUrl}/_cat/indices/${idx}?format=json`);
                if (!indexExistsResponse.ok) {
                  console.warn(`Index ${idx} does not exist, skipping`);
                  continue;
                }

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
                
                const response = await fetch(`${baseUrl}/${idx}/_search`, {
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
                                lte: lte
                              }
                            }
                          }
                        ]
                      }
                    },
                    sort: [{ timestamp: { order: 'asc' } }],
                    size: 10000
                  }),
                  signal: controller.signal
                });
                
                clearTimeout(timeoutId);

                if (response.ok) {
                  const result: ESResponse<T> = await response.json();
                  const mappedData = result.hits.hits.map(h => ({
                    ...h._source,
                    sourceIndex: idx // Add source index for color coding
                  }));
                  allData = [...allData, ...mappedData];
                } else {
                  console.warn(`Failed to fetch data from index ${idx}: HTTP ${response.status}`);
                }
              } catch (error) {
                console.warn(`Failed to fetch data from index ${idx}:`, error);
                // Continue with other indices even if one fails
              }
            }
            
            // Sort combined data by timestamp
            allData.sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
            setData(allData);
            return; // Exit early to avoid single index logic
          }
        }
        
        // Single index query (original logic)
        if (index !== 'all') {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
          
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
                          lte: lte
                        }
                      }
                    }
                  ]
                }
              },
              sort: [{ timestamp: { order: 'asc' } }],
              size: 10000
            }),
            signal: controller.signal
          });
          
          clearTimeout(timeoutId);

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const result: ESResponse<T> = await response.json();
          const mappedData = result.hits.hits.map(h => ({
            ...h._source,
            sourceIndex: index // Add source index for color coding
          }));
          
          // If no data found with timestamp filter, try without timestamp filter for debugging
          if (mappedData.length === 0 && startDate && endDate) {
            const fallbackResponse = await fetch(`${baseUrl}/${index}/_search`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                query: {
                  query_string: { query }
                },
          sort: [{ timestamp: { order: 'desc' } }],
                size: 10
              })
            });
            
            if (fallbackResponse.ok) {
              const fallbackResult: ESResponse<T> = await fallbackResponse.json();
              const fallbackData = fallbackResult.hits.hits.map(h => h._source);
              if (fallbackData.length > 0) {
                // Try a broader time range to see if we can get data
                const broaderStart = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(); // 24 hours ago
                const broaderEnd = new Date(Date.now() + 60 * 60 * 1000).toISOString(); // 1 hour from now
              }
            }
          }
          
          setData(mappedData);
        } else {
          // Fallback case: if index === 'all' but no lab indices found, show empty data
          console.warn('No valid indices found for "all" selection');
          setData([]);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
        setData([]);
      } finally {
        setIsLoading(false);
      }
    };

    // Add debounce to prevent rapid successive calls
    const timeoutId = setTimeout(fetchData, 300);
    return () => clearTimeout(timeoutId);
  }, [baseUrl, index, query, startDate, endDate, availableIndices]);

  return { data, isLoading };
}

export default function App() {
  const baseUrl = '/es';
  const [index, setIndex] = useState<string>('lab_monitoring');
  const [availableIndices, setAvailableIndices] = useState<string[]>(['lab_monitoring']);
  const [loadingIndices, setLoadingIndices] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>('overview');

  // Auto-refresh state
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(0); // 0 = off
  const [refreshKey, setRefreshKey] = useState<number>(0);

  // Dark mode state (load from localStorage)
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  // Comparison mode state
  const [comparisonMode, setComparisonMode] = useState<boolean>(false);
  const [comparisonDateRange, setComparisonDateRange] = useState<{start: string, end: string}>({
    start: '',
    end: ''
  });

  // View mode state (chart vs table)
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');

  // Show statistics toggle
  const [showStats, setShowStats] = useState<boolean>(false);

  // Alert system state
  const [alertRules, setAlertRules] = useState<AlertRule[]>(() => {
    const saved = localStorage.getItem('alertRules');
    return saved ? JSON.parse(saved) : [
      {
        id: '1',
        name: 'High CPU Usage',
        metric: 'cpu',
        condition: 'above',
        threshold: 80,
        enabled: true,
        tab: 'overview'
      },
      {
        id: '2',
        name: 'Low Memory',
        metric: 'memory',
        condition: 'below',
        threshold: 20,
        enabled: true,
        tab: 'overview'
      }
    ];
  });
  const [activeAlerts, setActiveAlerts] = useState<AlertTrigger[]>([]);
  const [showAlertPanel, setShowAlertPanel] = useState<boolean>(false);

  // Save alert rules to localStorage
  useEffect(() => {
    localStorage.setItem('alertRules', JSON.stringify(alertRules));
  }, [alertRules]);

  // Function to fetch available indices matching lab_mon* pattern
  const fetchAvailableIndices = async () => {
    setLoadingIndices(true);
    try {
      const response = await fetch(`${baseUrl}/_cat/indices/lab_mon*?format=json`);
      if (response.ok) {
        const indices = await response.json();
        const indexNames = indices.map((idx: any) => idx.index).filter((name: string) => name.startsWith('lab_mon'));
        if (indexNames.length > 0) {
          setAvailableIndices(['all', ...indexNames]);
        } else {
          console.warn('No lab_mon* indices found, using default');
          setAvailableIndices(['lab_monitoring', 'all']);
        }
      } else {
        console.error('Failed to fetch indices:', response.statusText);
        // Fallback to default indices
        setAvailableIndices(['lab_monitoring', 'all']);
      }
    } catch (error) {
      console.error('Error fetching indices:', error);
      // Fallback to default indices
      setAvailableIndices(['lab_monitoring', 'all']);
    } finally {
      setLoadingIndices(false);
    }
  };
  const [isGeneratingPDF, setIsGeneratingPDF] = useState<boolean>(false);
  // Helper function to format date for datetime-local input (local timezone)
  const formatDateForInput = useCallback((date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }, []);

  const [dateRange, setDateRange] = useState<{start: string, end: string}>(() => {
    const now = new Date();
    const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    return {
      start: formatDateForInput(sevenDaysAgo), // 7 days ago in local timezone
      end: formatDateForInput(now) // Current time in local timezone
    };
  });
  const [showCustomDateFilter, setShowCustomDateFilter] = useState<boolean>(false);
  
  // Track the currently selected time preset
  const [selectedTimePreset, setSelectedTimePreset] = useState<string>('7d');

  const dashboardRef = useRef<HTMLDivElement>(null);

  // Fetch available indices on component mount
  useEffect(() => {
    fetchAvailableIndices();
  }, []);

  // Auto-refresh mechanism
  useEffect(() => {
    if (autoRefreshInterval === 0) return; // No refresh if disabled

    const intervalId = setInterval(() => {
      setRefreshKey(prev => prev + 1); // Trigger re-fetch by changing key
    }, autoRefreshInterval);

    return () => clearInterval(intervalId);
  }, [autoRefreshInterval]);

  // Dark mode persistence
  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    // Apply dark mode class to body
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [darkMode]);

  // Save user preferences to localStorage
  useEffect(() => {
    const preferences = {
      autoRefreshInterval,
      darkMode,
      selectedTimePreset,
      activeTab
    };
    localStorage.setItem('userPreferences', JSON.stringify(preferences));
  }, [autoRefreshInterval, darkMode, activeTab]);

  // Load user preferences on mount
  useEffect(() => {
    const saved = localStorage.getItem('userPreferences');
    if (saved) {
      try {
        const prefs = JSON.parse(saved);
        if (prefs.autoRefreshInterval !== undefined) setAutoRefreshInterval(prefs.autoRefreshInterval);
        if (prefs.activeTab) setActiveTab(prefs.activeTab);
      } catch (e) {
        console.error('Failed to load user preferences:', e);
      }
    }
  }, []);

  // Custom date filter handler
  const handleCustomDateChange = useCallback((field: 'start' | 'end', value: string) => {
    // Clear the selected preset when using custom dates
    setSelectedTimePreset('custom');
    
    setDateRange(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  // Convert date range strings to Date objects (memoized to prevent unnecessary re-renders)
  // Parse as local timezone to match user's browser timezone
  const startDate = useMemo(() => {
    const dateStr = dateRange.start + ':00';
    const date = new Date(dateStr);
    return date;
  }, [dateRange.start]);
  
  const endDate = useMemo(() => {
    const dateStr = dateRange.end + ':00';
    const date = new Date(dateStr);
    return date;
  }, [dateRange.end]);

  // Data fetching with new comprehensive data sources (using debounced dates)
  const perf = useESWithDateFilter<PerfDoc>(baseUrl, index, 'event_type:performance_metrics', debouncedStartDate, debouncedEndDate, availableIndices);
  const cmds = useESWithDateFilter<CommandDoc>(
    baseUrl,
    index,
    'event_type:monitoring_summary',
    debouncedStartDate,
    debouncedEndDate,
    availableIndices
  );
  const windows = useESWithDateFilter<WindowUsageDoc>(baseUrl, index, 'event_type:user_activity', debouncedStartDate, debouncedEndDate, availableIndices);

  // New engagement data sources
  const engagementSessions = useESWithDateFilter<EngagementSessionDoc>(baseUrl, index, 'event_type:engagement_session', debouncedStartDate, debouncedEndDate, availableIndices);
  // Pull command activity from both direct command events and monitoring summaries
  const commandEngagement = useESWithDateFilter<CommandDoc>(
    baseUrl,
    index,
    'event_type:monitoring_summary',
    debouncedStartDate,
    debouncedEndDate,
    availableIndices
  );
  const learningProgress = useESWithDateFilter<LearningProgressDoc>(baseUrl, index, 'event_type:learning_progress', debouncedStartDate, debouncedEndDate, availableIndices);
  const appUsageStats = useESWithDateFilter<AppUsageDoc>(baseUrl, index, 'event_type:app_usage_stats', debouncedStartDate, debouncedEndDate, availableIndices);
  const dailyActivity = useESWithDateFilter<DailyActivityDoc>(baseUrl, index, 'event_type:daily_activity', debouncedStartDate, debouncedEndDate, availableIndices);
  const engagementMetrics = useESWithDateFilter<EngagementSessionDoc>(baseUrl, index, 'event_type:engagement_metrics', debouncedStartDate, debouncedEndDate, availableIndices);
  const skillProgressAnalytics = useESWithDateFilter<LearningProgressDoc>(baseUrl, index, 'event_type:skill_progress_analytics', debouncedStartDate, debouncedEndDate, availableIndices);
  const skillCrossComparison = useESWithDateFilter<LearningProgressDoc>(baseUrl, index, 'event_type:skill_cross_comparison', debouncedStartDate, debouncedEndDate, availableIndices);
  const dropoutRiskAssessment = useESWithDateFilter<DropoutRiskDoc>(baseUrl, index, 'event_type:dropout_risk_assessment', debouncedStartDate, debouncedEndDate, availableIndices);
  const crossServerMetrics = useESWithDateFilter<CrossServerDoc>(baseUrl, index, 'event_type:cross_server_metrics', debouncedStartDate, debouncedEndDate, availableIndices);
  const crossServerComparison = useESWithDateFilter<CrossServerDoc>(baseUrl, index, 'event_type:cross_server_comparison', debouncedStartDate, debouncedEndDate, availableIndices);

  // New monitoring module data hooks
  const filesystemData = useESWithDateFilter<FileSystemDoc>(baseUrl, index, 'event_type:filesystem_activity', debouncedStartDate, debouncedEndDate, availableIndices);
  const errorDebugData = useESWithDateFilter<ErrorDebugDoc>(baseUrl, index, 'event_type:error_debug', debouncedStartDate, debouncedEndDate, availableIndices);
  const devEnvironmentData = useESWithDateFilter<DevEnvironmentDoc>(baseUrl, index, 'event_type:dev_environment', debouncedStartDate, debouncedEndDate, availableIndices);
  const browserActivityData = useESWithDateFilter<BrowserActivityDoc>(baseUrl, index, 'event_type:browser_activity', debouncedStartDate, debouncedEndDate, availableIndices);
  const codeQualityData = useESWithDateFilter<CodeQualityDoc>(baseUrl, index, 'event_type:code_quality', debouncedStartDate, debouncedEndDate, availableIndices);
  const packageDependencyData = useESWithDateFilter<PackageDependencyDoc>(baseUrl, index, 'event_type:package_dependency', debouncedStartDate, debouncedEndDate, availableIndices);
  const collaborationData = useESWithDateFilter<CollaborationDoc>(baseUrl, index, 'event_type:collaboration', debouncedStartDate, debouncedEndDate, availableIndices);
  const learningPathData = useESWithDateFilter<LearningPathDoc>(baseUrl, index, 'event_type:learning_path', debouncedStartDate, debouncedEndDate, availableIndices);
  const resourceAccessData = useESWithDateFilter<ResourceAccessDoc>(baseUrl, index, 'event_type:resource_access', debouncedStartDate, debouncedEndDate, availableIndices);
  const timeDistributionData = useESWithDateFilter<TimeDistributionDoc>(baseUrl, index, 'event_type:time_distribution', debouncedStartDate, debouncedEndDate, availableIndices);
  const hardwareUtilizationData = useESWithDateFilter<HardwareUtilizationDoc>(baseUrl, index, 'event_type:hardware_utilization', debouncedStartDate, debouncedEndDate, availableIndices);
  const networkBehaviorData = useESWithDateFilter<NetworkBehaviorDoc>(baseUrl, index, 'event_type:network_behavior', debouncedStartDate, debouncedEndDate, availableIndices);
  const terminalConsoleData = useESWithDateFilter<TerminalConsoleDoc>(baseUrl, index, 'event_type:terminal_console', debouncedStartDate, debouncedEndDate, availableIndices);
  const projectLifecycleData = useESWithDateFilter<ProjectLifecycleDoc>(baseUrl, index, 'event_type:project_lifecycle', debouncedStartDate, debouncedEndDate, availableIndices);

  const isLoading = useMemo(() =>
    perf.isLoading || cmds.isLoading || windows.isLoading ||
    engagementSessions.isLoading || commandEngagement.isLoading || learningProgress.isLoading ||
    appUsageStats.isLoading || dailyActivity.isLoading || engagementMetrics.isLoading ||
    skillProgressAnalytics.isLoading || skillCrossComparison.isLoading || dropoutRiskAssessment.isLoading ||
    crossServerMetrics.isLoading || crossServerComparison.isLoading ||
    filesystemData.isLoading || errorDebugData.isLoading || devEnvironmentData.isLoading ||
    browserActivityData.isLoading || codeQualityData.isLoading || packageDependencyData.isLoading ||
    collaborationData.isLoading || learningPathData.isLoading || resourceAccessData.isLoading ||
    timeDistributionData.isLoading || hardwareUtilizationData.isLoading || networkBehaviorData.isLoading ||
    terminalConsoleData.isLoading || projectLifecycleData.isLoading,
    [perf.isLoading, cmds.isLoading, windows.isLoading,
     engagementSessions.isLoading, commandEngagement.isLoading, learningProgress.isLoading,
     appUsageStats.isLoading, dailyActivity.isLoading, engagementMetrics.isLoading,
     skillProgressAnalytics.isLoading, skillCrossComparison.isLoading, dropoutRiskAssessment.isLoading,
     crossServerMetrics.isLoading, crossServerComparison.isLoading,
     filesystemData.isLoading, errorDebugData.isLoading, devEnvironmentData.isLoading,
     browserActivityData.isLoading, codeQualityData.isLoading, packageDependencyData.isLoading,
     collaborationData.isLoading, learningPathData.isLoading, resourceAccessData.isLoading,
     timeDistributionData.isLoading, hardwareUtilizationData.isLoading, networkBehaviorData.isLoading,
     terminalConsoleData.isLoading, projectLifecycleData.isLoading]
  );

  // Time filter handler with debouncing
  const handleTimePresetChange = useCallback((preset: string) => {
    // Update the selected preset state
    setSelectedTimePreset(preset);
    
    // Use local timezone for all calculations to match user's browser timezone
    const now = new Date();
    let startDate: Date;

    switch (preset) {
      case '1h':
        startDate = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case '2h':
        startDate = new Date(now.getTime() - 2 * 60 * 60 * 1000);
        break;
      case '6h':
        startDate = new Date(now.getTime() - 6 * 60 * 60 * 1000);
        break;
      case '1d':
        startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    }

    // Add some buffer to the end time to ensure we catch recent data
    const endDate = new Date(now.getTime() + 5 * 60 * 1000); // 5 minutes buffer

    // Convert to local datetime-local format (YYYY-MM-DDTHH:MM) using local timezone
    const startLocal = formatDateForInput(startDate);
    const endLocal = formatDateForInput(endDate);

    setDateRange({
      start: startLocal,
      end: endLocal
    });
  }, []);

  // PDF download function
  const downloadPDF = async () => {
    if (!dashboardRef.current) return;
    
    setIsGeneratingPDF(true);
    try {
      const { default: jsPDF } = await import('jspdf');
      const { default: html2canvas } = await import('html2canvas');
      
      const pdf = new jsPDF('p', 'mm', 'a4');
      let isFirstPage = true;
      
      // Capture charts from all tabs by temporarily switching to each tab
      for (const tab of tabs) {
        // Switch to this tab temporarily
        const originalActiveTab = activeTab;
        setActiveTab(tab.id);
        
        // Wait for the tab to render
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Add new page for each tab (except the first one)
        if (!isFirstPage) {
          pdf.addPage();
        }
        isFirstPage = false;
        
        // Add page title
        pdf.setFontSize(20);
        pdf.text(`${tab.label}`, 20, 20);
        
        // Add timestamp and time range info
        pdf.setFontSize(10);
        pdf.text(`Generated on: ${new Date().toLocaleString()}`, 20, 30);
        pdf.text(`Time Range: ${dateRange.start} to ${dateRange.end}`, 20, 35);
        
        // Capture the current tab content
        const tabContent = dashboardRef.current.querySelector('[data-tab-content]');
        if (tabContent) {
          const canvas = await html2canvas(tabContent as HTMLElement, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            logging: false
          });
          
          // Calculate dimensions to fit the page nicely
          const pageWidth = 210; // A4 width in mm
          const pageHeight = 297; // A4 height in mm
          const margin = 20;
          const availableWidth = pageWidth - (2 * margin);
          const availableHeight = pageHeight - 60; // Leave space for header
          
          const imgWidth = availableWidth;
          const imgHeight = (canvas.height * imgWidth) / canvas.width;
          
          // If image is too tall, scale it down
          const finalHeight = imgHeight > availableHeight ? availableHeight : imgHeight;
          const finalWidth = finalHeight === imgHeight ? imgWidth : (canvas.width * finalHeight) / canvas.height;
          
          // Center the image horizontally
          const xPosition = (pageWidth - finalWidth) / 2;
          
          // Add chart image to PDF
          pdf.addImage(canvas.toDataURL('image/png'), 'PNG', xPosition, 45, finalWidth, finalHeight);
        }
        
        // Restore original tab
        setActiveTab(originalActiveTab);
        
        // Wait a bit before switching to next tab
        await new Promise(resolve => setTimeout(resolve, 200));
      }
      
      pdf.save('dashboard-report.pdf');
    } catch (error) {
      console.error('Error generating PDF:', error);
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  // Export current tab charts as individual PNG files
  const exportChartsAsPNG = async () => {
    if (!dashboardRef.current) return;

    setIsGeneratingPDF(true); // Reuse the same loading state
    try {
      const { default: html2canvas } = await import('html2canvas');

      // Find all ResponsiveContainer divs (chart containers) in the current tab
      const tabContent = dashboardRef.current.querySelector('[data-tab-content]');
      if (!tabContent) {
        console.error('Tab content not found');
        return;
      }

      // Get all chart containers - they're the ResponsiveContainer divs
      const chartContainers = tabContent.querySelectorAll('.recharts-responsive-container');

      if (chartContainers.length === 0) {
        alert('No charts found in the current tab');
        return;
      }

      // Export each chart
      for (let i = 0; i < chartContainers.length; i++) {
        const container = chartContainers[i] as HTMLElement;

        // Find the parent heading to use as filename
        let chartTitle = `chart-${i + 1}`;
        let parent = container.parentElement;
        while (parent && parent !== tabContent) {
          const heading = parent.querySelector('h3, h4');
          if (heading) {
            chartTitle = heading.textContent?.trim().replace(/[^a-zA-Z0-9-]/g, '_') || chartTitle;
            break;
          }
          parent = parent.parentElement;
        }

        try {
          const canvas = await html2canvas(container, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: darkMode ? '#1a1a1a' : '#ffffff',
            logging: false
          });

          // Convert to blob and download
          canvas.toBlob((blob) => {
            if (blob) {
              const url = URL.createObjectURL(blob);
              const link = document.createElement('a');
              link.href = url;
              link.download = `${activeTab}-${chartTitle}.png`;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              URL.revokeObjectURL(url);
            }
          }, 'image/png');

          // Small delay between downloads to avoid browser blocking
          await new Promise(resolve => setTimeout(resolve, 100));
        } catch (error) {
          console.error(`Error exporting chart ${i + 1}:`, error);
        }
      }

    } catch (error) {
      console.error('Error exporting charts:', error);
      alert('Error exporting charts. Please try again.');
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  // CSV Export utility function
  const exportToCSV = (data: any[], filename: string) => {
    if (data.length === 0) {
      alert('No data to export');
      return;
    }

    // Get all unique keys from data
    const keys = Array.from(
      new Set(data.flatMap(obj => Object.keys(obj)))
    ).filter(key => typeof data[0][key] !== 'object'); // Exclude nested objects

    // Create CSV header
    const header = keys.join(',');

    // Create CSV rows
    const rows = data.map(row => {
      return keys.map(key => {
        const value = row[key];
        // Handle values that might contain commas or quotes
        if (value === null || value === undefined) return '';
        const stringValue = String(value);
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      }).join(',');
    }).join('\n');

    // Combine header and rows
    const csv = `${header}\n${rows}`;

    // Create blob and download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Export all current tab data as CSV
  const exportCurrentTabData = () => {
    const dataMap: Record<string, { data: any[], name: string }> = {
      'overview': { data: perfData, name: 'performance-metrics' },
      'engagement': { data: engagementData, name: 'engagement-analytics' },
      'learning': { data: learningProgress.data, name: 'learning-progress' },
      'usage': { data: appUsageStats.data, name: 'app-usage' },
      'risk': { data: dropoutRiskAssessment.data, name: 'risk-assessment' },
      'comparison': { data: crossServerMetrics.data, name: 'cross-server-metrics' },
      'security': { data: commands.data, name: 'security-commands' },
      'analytics': { data: dailyActivity.data, name: 'daily-activity' },
      'developer': {
        data: [
          ...filesystemData.data,
          ...errorDebugData.data,
          ...devEnvironmentData.data,
          ...browserActivityData.data,
          ...codeQualityData.data,
          ...packageDependencyData.data,
          ...collaborationData.data,
          ...learningPathData.data,
          ...resourceAccessData.data,
          ...timeDistributionData.data,
          ...hardwareUtilizationData.data,
          ...networkBehaviorData.data,
          ...terminalConsoleData.data,
          ...projectLifecycleData.data
        ],
        name: 'developer-insights'
      }
    };

    const tabData = dataMap[activeTab];
    if (tabData && tabData.data.length > 0) {
      const timestamp = new Date().toISOString().split('T')[0];
      exportToCSV(tabData.data, `${tabData.name}-${timestamp}`);
    } else {
      alert('No data available to export for this tab');
    }
  };

  // URL State Management - for shareable dashboard links
  useEffect(() => {
    // Load state from URL on mount
    const params = new URLSearchParams(window.location.search);

    if (params.has('index')) setIndex(params.get('index')!);
    if (params.has('tab')) setActiveTab(params.get('tab')!);
    if (params.has('startDate')) setStartDate(new Date(params.get('startDate')!));
    if (params.has('endDate')) setEndDate(new Date(params.get('endDate')!));
    if (params.has('preset')) setSelectedTimePreset(params.get('preset')!);
    if (params.has('darkMode')) setDarkMode(params.get('darkMode') === 'true');
    if (params.has('refresh')) setAutoRefreshInterval(Number(params.get('refresh')));
  }, []);

  // Update URL when state changes
  useEffect(() => {
    const params = new URLSearchParams();
    params.set('index', index);
    params.set('tab', activeTab);
    params.set('startDate', startDate.toISOString());
    params.set('endDate', endDate.toISOString());
    params.set('preset', selectedTimePreset);
    params.set('darkMode', String(darkMode));
    params.set('refresh', String(autoRefreshInterval));

    // Update URL without reloading the page
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', newUrl);
  }, [index, activeTab, startDate, endDate, selectedTimePreset, darkMode, autoRefreshInterval]);

  // Copy shareable link to clipboard
  const copyShareableLink = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
      alert('Dashboard link copied to clipboard! Share it to preserve current view settings.');
    }).catch(() => {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = url;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      alert('Dashboard link copied to clipboard!');
    });
  };

  // Debounce utility hook
  const useDebounce = <T,>(value: T, delay: number): T => {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
      const handler = setTimeout(() => {
        setDebouncedValue(value);
      }, delay);

      return () => {
        clearTimeout(handler);
      };
    }, [value, delay]);

    return debouncedValue;
  };

  // Debounced date values to reduce API calls
  const debouncedStartDate = useDebounce(startDate, 500);
  const debouncedEndDate = useDebounce(endDate, 500);

  // Statistical calculation utilities
  const calculateStats = (values: number[]) => {
    if (values.length === 0) return null;

    const sorted = [...values].sort((a, b) => a - b);
    const sum = values.reduce((a, b) => a + b, 0);
    const mean = sum / values.length;

    // Median
    const mid = Math.floor(sorted.length / 2);
    const median = sorted.length % 2 === 0
      ? (sorted[mid - 1] + sorted[mid]) / 2
      : sorted[mid];

    // Standard Deviation
    const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    // Percentiles
    const getPercentile = (p: number) => {
      const index = Math.ceil((p / 100) * sorted.length) - 1;
      return sorted[Math.max(0, index)];
    };

    return {
      count: values.length,
      mean: mean,
      median: median,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      stdDev: stdDev,
      p25: getPercentile(25),
      p50: median,
      p75: getPercentile(75),
      p90: getPercentile(90),
      p99: getPercentile(99)
    };
  };

  // Statistical Summary Cards Component
  const StatisticalSummary = ({ title, data, field }: { title: string, data: any[], field: string }) => {
    const values = data
      .map(d => {
        // Handle nested fields (e.g., 'data.cpu')
        const keys = field.split('.');
        let value = d;
        for (const key of keys) {
          value = value?.[key];
        }
        return typeof value === 'number' ? value : null;
      })
      .filter((v): v is number => v !== null);

    const stats = calculateStats(values);

    if (!stats) {
      return (
        <div style={{
          padding: 16,
          backgroundColor: darkMode ? '#2d2d2d' : '#f9f9f9',
          borderRadius: 8,
          border: `1px solid ${darkMode ? '#444' : '#ddd'}`
        }}>
          <h4 style={{ marginTop: 0 }}>{title}</h4>
          <p style={{ color: darkMode ? '#888' : '#999' }}>No data available</p>
        </div>
      );
    }

    return (
      <div style={{
        padding: 16,
        backgroundColor: darkMode ? '#2d2d2d' : '#ffffff',
        borderRadius: 8,
        border: `1px solid ${darkMode ? '#444' : '#ddd'}`,
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h4 style={{ marginTop: 0, marginBottom: 16, color: darkMode ? '#e0e0e0' : '#333' }}>{title}</h4>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
          gap: 12
        }}>
          <div>
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginBottom: 4 }}>Count</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: darkMode ? '#e0e0e0' : '#333' }}>
              {stats.count}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginBottom: 4 }}>Mean</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#2196f3' }}>
              {stats.mean.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginBottom: 4 }}>Median</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#4caf50' }}>
              {stats.median.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginBottom: 4 }}>Min</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#ff9800' }}>
              {stats.min.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginBottom: 4 }}>Max</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#f44336' }}>
              {stats.max.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginBottom: 4 }}>Std Dev</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#9c27b0' }}>
              {stats.stdDev.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginBottom: 4 }}>P25</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: darkMode ? '#ccc' : '#666' }}>
              {stats.p25.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginBottom: 4 }}>P75</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: darkMode ? '#ccc' : '#666' }}>
              {stats.p75.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginBottom: 4 }}>P90</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: darkMode ? '#ccc' : '#666' }}>
              {stats.p90.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: darkMode ? '#888' : '#999', marginBottom: 4 }}>P99</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: darkMode ? '#ccc' : '#666' }}>
              {stats.p99.toFixed(2)}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Alert evaluation - check if any rules are triggered
  useEffect(() => {
    const evaluateAlerts = () => {
      const newAlerts: AlertTrigger[] = [];

      alertRules.filter(rule => rule.enabled).forEach(rule => {
        if (rule.tab === 'overview' && rule.metric === 'cpu') {
          const latestCPU = perf.data[perf.data.length - 1]?.data?.cpu?.utilization_percent;
          if (latestCPU !== undefined) {
            const triggered = rule.condition === 'above'
              ? latestCPU > rule.threshold
              : latestCPU < rule.threshold;

            if (triggered) {
              newAlerts.push({
                ruleId: rule.id,
                ruleName: rule.name,
                value: latestCPU,
                threshold: rule.threshold,
                timestamp: new Date()
              });
            }
          }
        }
        if (rule.tab === 'overview' && rule.metric === 'memory') {
          const latestMemory = perf.data[perf.data.length - 1]?.data?.memory?.ram_percent;
          if (latestMemory !== undefined) {
            const triggered = rule.condition === 'above'
              ? latestMemory > rule.threshold
              : latestMemory < rule.threshold;

            if (triggered) {
              newAlerts.push({
                ruleId: rule.id,
                ruleName: rule.name,
                value: latestMemory,
                threshold: rule.threshold,
                timestamp: new Date()
              });
            }
          }
        }
      });

      setActiveAlerts(newAlerts);

      // Browser notification if alerts are triggered
      if (newAlerts.length > 0 && 'Notification' in window && Notification.permission === 'granted') {
        new Notification('Dashboard Alert', {
          body: `${newAlerts.length} alert(s) triggered`,
          icon: '⚠️'
        });
      }
    };

    evaluateAlerts();
  }, [perf.data, alertRules]);

  // Alert Panel Component
  const AlertPanel = () => (
    <div style={{
      position: 'fixed',
      top: 0,
      right: showAlertPanel ? 0 : '-400px',
      width: '400px',
      height: '100vh',
      backgroundColor: darkMode ? '#2d2d2d' : 'white',
      boxShadow: '-2px 0 8px rgba(0,0,0,0.2)',
      transition: 'right 0.3s ease',
      zIndex: 2000,
      overflowY: 'auto',
      padding: 20
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
        borderBottom: `2px solid ${darkMode ? '#444' : '#ddd'}`,
        paddingBottom: 12
      }}>
        <h3 style={{ margin: 0 }}>Alert Configuration</h3>
        <button
          onClick={() => setShowAlertPanel(false)}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '24px',
            cursor: 'pointer',
            color: darkMode ? '#e0e0e0' : '#333'
          }}
        >
          ×
        </button>
      </div>

      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ color: '#f44336', marginBottom: 12 }}>⚠️ Active Alerts ({activeAlerts.length})</h4>
          {activeAlerts.map((alert, idx) => (
            <div key={idx} style={{
              padding: 12,
              backgroundColor: darkMode ? '#3d2020' : '#ffebee',
              borderLeft: '4px solid #f44336',
              marginBottom: 8,
              borderRadius: 4
            }}>
              <div style={{ fontWeight: 'bold', color: '#f44336' }}>{alert.ruleName}</div>
              <div style={{ fontSize: '12px', marginTop: 4, color: darkMode ? '#ccc' : '#666' }}>
                Value: {alert.value.toFixed(2)} | Threshold: {alert.threshold}
              </div>
              <div style={{ fontSize: '11px', marginTop: 2, color: darkMode ? '#888' : '#999' }}>
                {alert.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Alert Rules */}
      <h4>Alert Rules</h4>
      {alertRules.map((rule) => (
        <div key={rule.id} style={{
          padding: 12,
          backgroundColor: darkMode ? '#3d3d3d' : '#f9f9f9',
          borderRadius: 4,
          marginBottom: 12,
          border: `1px solid ${darkMode ? '#555' : '#ddd'}`
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 'bold' }}>{rule.name}</span>
            <input
              type="checkbox"
              checked={rule.enabled}
              onChange={(e) => {
                setAlertRules(alertRules.map(r =>
                  r.id === rule.id ? { ...r, enabled: e.target.checked } : r
                ));
              }}
              style={{ width: 20, height: 20, cursor: 'pointer' }}
            />
          </div>
          <div style={{ fontSize: '12px', marginTop: 8, color: darkMode ? '#bbb' : '#666' }}>
            {rule.metric} {rule.condition} {rule.threshold}
          </div>
        </div>
      ))}

      {/* Request Notification Permission */}
      {'Notification' in window && Notification.permission === 'default' && (
        <button
          onClick={() => Notification.requestPermission()}
          style={{
            width: '100%',
            padding: '12px',
            backgroundColor: '#2196f3',
            color: 'white',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            marginTop: 16
          }}
        >
          Enable Browser Notifications
        </button>
      )}
    </div>
  );

  // Data Table component for table view
  const DataTable = ({ data, maxRows = 100 }: { data: any[], maxRows?: number }) => {
    if (data.length === 0) {
      return <NoDataMessage message="No data available to display in table view" />;
    }

    // Get all unique keys from the data
    const allKeys = Array.from(
      new Set(data.flatMap(obj => Object.keys(obj)))
    ).filter(key => {
      // Exclude complex nested objects for table view
      const sampleValue = data.find(d => d[key])?.[key];
      return typeof sampleValue !== 'object' || sampleValue === null;
    });

    const displayData = data.slice(0, maxRows);

    return (
      <div style={{ overflowX: 'auto', marginTop: 16 }}>
        <div style={{
          marginBottom: 12,
          color: darkMode ? '#bbb' : '#666',
          fontSize: '14px'
        }}>
          Showing {displayData.length} of {data.length} records
          {data.length > maxRows && ` (limited to first ${maxRows} rows)`}
        </div>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          backgroundColor: darkMode ? '#2d2d2d' : 'white',
          border: `1px solid ${darkMode ? '#444' : '#ddd'}`
        }}>
          <thead>
            <tr style={{
              backgroundColor: darkMode ? '#3d3d3d' : '#f5f5f5',
              borderBottom: `2px solid ${darkMode ? '#555' : '#ddd'}`
            }}>
              {allKeys.map(key => (
                <th key={key} style={{
                  padding: '12px 8px',
                  textAlign: 'left',
                  fontWeight: 'bold',
                  color: darkMode ? '#e0e0e0' : '#333',
                  fontSize: '14px',
                  whiteSpace: 'nowrap'
                }}>
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.map((row, rowIndex) => (
              <tr key={rowIndex} style={{
                borderBottom: `1px solid ${darkMode ? '#444' : '#eee'}`,
                '&:hover': {
                  backgroundColor: darkMode ? '#3a3a3a' : '#f9f9f9'
                }
              }}>
                {allKeys.map(key => (
                  <td key={key} style={{
                    padding: '10px 8px',
                    color: darkMode ? '#ccc' : '#555',
                    fontSize: '13px',
                    maxWidth: '200px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {row[key] !== null && row[key] !== undefined
                      ? String(row[key])
                      : '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Loading Skeleton component
  const LoadingSkeleton = () => (
    <div style={{ padding: 16 }}>
      <div className="skeleton skeleton-title"></div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
        <div className="skeleton skeleton-chart"></div>
        <div className="skeleton skeleton-chart"></div>
        <div className="skeleton skeleton-chart"></div>
        <div className="skeleton skeleton-chart"></div>
      </div>
      <div style={{ marginTop: 20 }}>
        <div className="skeleton skeleton-text" style={{ width: '40%' }}></div>
        <div className="skeleton skeleton-text" style={{ width: '60%' }}></div>
        <div className="skeleton skeleton-text" style={{ width: '50%' }}></div>
      </div>
    </div>
  );

  // No Data component
  const NoDataMessage = ({ message = "No data available for the selected time range" }: { message?: string }) => (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '400px',
      backgroundColor: darkMode ? '#2d2d2d' : '#f9f9f9',
      borderRadius: 8,
      border: `2px dashed ${darkMode ? '#444' : '#ddd'}`,
      padding: 32
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '4em', marginBottom: 16 }}>📊</div>
        <p style={{
          color: darkMode ? '#bbb' : '#666',
          fontSize: '1.2em',
          marginBottom: 8,
          fontWeight: 600
        }}>
          {message}
        </p>
        <p style={{
          color: darkMode ? '#888' : '#999',
          fontSize: '0.9em',
          marginBottom: 16
        }}>
          Try selecting a different time range or index
        </p>
        <div style={{
          display: 'flex',
          gap: 8,
          justifyContent: 'center',
          marginTop: 20
        }}>
          <div style={{
            padding: '8px 16px',
            backgroundColor: darkMode ? '#3d3d3d' : '#e3f2fd',
            borderRadius: 4,
            fontSize: '0.85em',
            color: darkMode ? '#bbb' : '#1976d2'
          }}>
            💡 Tip: Check if data is being collected
          </div>
        </div>
      </div>
    </div>
  );

  // Color palette for different indices
  const getIndexColor = useCallback((indexName: string, colorIndex?: number) => {
    const colors = [
      '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00',
      '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
      '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43'
    ];
    
    if (colorIndex !== undefined) {
      return colors[colorIndex % colors.length];
    }
    
    // Generate consistent color based on index name
    let hash = 0;
    for (let i = 0; i < indexName.length; i++) {
      hash = indexName.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  }, []);

  // State for line visibility (clickable legend)
  const [visibleLines, setVisibleLines] = useState<Record<string, boolean>>({});
  
  // State for engagement graph visibility - start with all lines visible
  const [engagementVisibleLines, setEngagementVisibleLines] = useState<Record<string, boolean>>({
    'all': true,
    'duration': true,
    'activity': true
  });

  // State for engagement metrics visibility
  const [engagementMetricsVisibleLines, setEngagementMetricsVisibleLines] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Engagement Metrics when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(engagementMetrics.data);
    setEngagementMetricsVisibleLines(prev => {
      const newState = { ...prev };
      // Always ensure 'all' is true by default
      newState.all = true;
      // Ensure all indices and their metrics are visible by default
      availableIndices.forEach(idx => {
        newState[`duration_${idx}`] = true;
        newState[`activity_${idx}`] = true;
        newState[`engagement_${idx}`] = true;
      });
      return newState;
    });
  }, [engagementMetrics.data]);

  const toggleEngagementMetricsLineVisibility = useCallback((lineKey: string) => {
    setEngagementMetricsVisibleLines(prev => {
      const availableIndices = getUniqueIndices(engagementMetrics.data);
      
      // If only one index, no need for complex toggle logic
      if (availableIndices.length === 1) {
        return prev; // No change needed for single index
      }
      
      if (lineKey === 'all') {
        // If "all" is clicked and it's currently true, turn it off and turn on all individual lines
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[`duration_${idx}`] = true;
            newState[`activity_${idx}`] = true;
            newState[`engagement_${idx}`] = true;
          });
          return newState;
        } else {
          // If "all" is clicked and it's currently false, turn it on and turn off all individual lines
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[`duration_${idx}`] = false;
            newState[`activity_${idx}`] = false;
            newState[`engagement_${idx}`] = false;
          });
          return newState;
        }
      } else {
        // Individual metric clicked
        const newState = { ...prev };
        const wasOnlyVisible = prev[lineKey] === true && Object.values(prev).filter(v => v === true).length === 1;
        
        if (wasOnlyVisible) {
          // If this was the only visible line, show all lines
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[`duration_${idx}`] = true;
            newState[`activity_${idx}`] = true;
            newState[`engagement_${idx}`] = true;
          });
        } else {
          // Toggle this specific line
          newState[lineKey] = !prev[lineKey];
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [engagementMetrics.data]);

  // State for learning progress visibility
  const [learningProgressVisibleBars, setLearningProgressVisibleBars] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Learning Progress when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(learningProgress.data);
    setLearningProgressVisibleBars(prev => {
      const newState = { ...prev };
      // Always ensure 'all' is true by default
      newState.all = true;
      // Ensure all indices are visible by default
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [learningProgress.data]);

  const toggleLearningProgressBarVisibility = useCallback((barKey: string) => {
    setLearningProgressVisibleBars(prev => {
      const availableIndices = getUniqueIndices(learningProgress.data);
      
      // If only one index, no need for complex toggle logic
      if (availableIndices.length === 1) {
        return prev; // No change needed for single index
      }
      
      if (barKey === 'all') {
        // If "all" is clicked and it's currently true, turn it off and turn on all individual lines
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[idx] = true;
          });
          return newState;
        } else {
          // If "all" is clicked and it's currently false, turn it on and turn off all individual lines
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
          return newState;
        }
      } else {
        // Individual line clicked
        const newState = { ...prev };
        newState[barKey] = !newState[barKey];
        
        // If this was the last visible line, turn on "all"
        const visibleIndividualLines = availableIndices.filter(idx => newState[idx] === true);
        if (visibleIndividualLines.length === 0) {
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
        } else {
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [learningProgress.data]);

  // State for app usage visibility
  const [appUsageVisibleBars, setAppUsageVisibleBars] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for App Usage when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(appUsageStats.data);
    setAppUsageVisibleBars(prev => {
      const newState = { ...prev };
      // Always ensure 'all' is true by default
      newState.all = true;
      // Ensure all indices are visible by default
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [appUsageStats.data]);

  const toggleAppUsageBarVisibility = useCallback((barKey: string) => {
    setAppUsageVisibleBars(prev => {
      const availableIndices = getUniqueIndices(appUsageStats.data);
      
      // If only one index, no need for complex toggle logic
      if (availableIndices.length === 1) {
        return prev; // No change needed for single index
      }
      
      if (barKey === 'all') {
        // If "all" is clicked and it's currently true, turn it off and turn on all individual lines
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[idx] = true;
          });
          return newState;
        } else {
          // If "all" is clicked and it's currently false, turn it on and turn off all individual lines
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
          return newState;
        }
      } else {
        // Individual line clicked
        const newState = { ...prev };
        newState[barKey] = !newState[barKey];
        
        // If this was the last visible line, turn on "all"
        const visibleIndividualLines = availableIndices.filter(idx => newState[idx] === true);
        if (visibleIndividualLines.length === 0) {
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
        } else {
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [appUsageStats.data]);

  // State for skill analytics visibility
  const [skillAnalyticsVisibleLines, setSkillAnalyticsVisibleLines] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Skill Analytics when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(skillProgressAnalytics.data);
    setSkillAnalyticsVisibleLines(prev => {
      const newState = { ...prev };
      // Always ensure 'all' is true by default
      newState.all = true;
      // Ensure all indices are visible by default
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [skillProgressAnalytics.data]);

  const toggleSkillAnalyticsLineVisibility = useCallback((lineKey: string) => {
    setSkillAnalyticsVisibleLines(prev => {
      const availableIndices = getUniqueIndices(skillProgressAnalytics.data);
      
      // If only one index, no need for complex toggle logic
      if (availableIndices.length === 1) {
        return prev; // No change needed for single index
      }
      
      if (lineKey === 'all') {
        // If "all" is clicked and it's currently true, turn it off and turn on all individual lines
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[idx] = true;
          });
          return newState;
        } else {
          // If "all" is clicked and it's currently false, turn it on and turn off all individual lines
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
          return newState;
        }
      } else {
        // Individual line clicked
        const newState = { ...prev };
        newState[lineKey] = !newState[lineKey];
        
        // If this was the last visible line, turn on "all"
        const visibleIndividualLines = availableIndices.filter(idx => newState[idx] === true);
        if (visibleIndividualLines.length === 0) {
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
        } else {
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [skillProgressAnalytics.data]);

  // State for skill comparison visibility
  const [skillComparisonVisibleBars, setSkillComparisonVisibleBars] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Skill Comparison when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(skillCrossComparison.data);
    setSkillComparisonVisibleBars(prev => {
      const newState = { ...prev };
      newState.all = true;
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [skillCrossComparison.data]);

  const toggleSkillComparisonBarVisibility = useCallback((lineKey: string) => {
    setSkillComparisonVisibleBars(prev => {
      const availableIndices = getUniqueIndices(skillCrossComparison.data);
      
      if (availableIndices.length === 1) {
        return prev;
      }
      
      if (lineKey === 'all') {
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[idx] = true;
          });
          return newState;
        } else {
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
          return newState;
        }
      } else {
        const newState = { ...prev };
        newState[lineKey] = !newState[lineKey];
        
        const visibleIndividualLines = availableIndices.filter(idx => newState[idx] === true);
        if (visibleIndividualLines.length === 0) {
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
        } else {
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [skillCrossComparison.data]);

  // State for daily activity visibility
  const [dailyActivityVisibleLines, setDailyActivityVisibleLines] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Daily Activity when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(dailyActivity.data);
    setDailyActivityVisibleLines(prev => {
      const newState = { ...prev };
      newState.all = true;
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [dailyActivity.data]);

  const toggleDailyActivityLineVisibility = useCallback((lineKey: string) => {
    setDailyActivityVisibleLines(prev => {
      const availableIndices = getUniqueIndices(dailyActivity.data);
      
      if (availableIndices.length === 1) {
        return prev;
      }
      
      if (lineKey === 'all') {
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[idx] = true;
          });
          return newState;
        } else {
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
          return newState;
        }
      } else {
        const newState = { ...prev };
        newState[lineKey] = !newState[lineKey];
        
        const visibleIndividualLines = availableIndices.filter(idx => newState[idx] === true);
        if (visibleIndividualLines.length === 0) {
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
        } else {
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [dailyActivity.data]);

  // State for window usage visibility
  const [windowUsageVisibleLines, setWindowUsageVisibleLines] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Window Usage when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(windows.data);
    setWindowUsageVisibleLines(prev => {
      const newState = { ...prev };
      newState.all = true;
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [windows.data]);

  const toggleWindowUsageLineVisibility = useCallback((lineKey: string) => {
    setWindowUsageVisibleLines(prev => {
      const availableIndices = getUniqueIndices(windows.data);
      
      if (availableIndices.length === 1) {
        return prev;
      }
      
      if (lineKey === 'all') {
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[idx] = true;
          });
          return newState;
        } else {
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
          return newState;
        }
      } else {
        const newState = { ...prev };
        newState[lineKey] = !newState[lineKey];
        
        const visibleIndividualLines = availableIndices.filter(idx => newState[idx] === true);
        if (visibleIndividualLines.length === 0) {
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
        } else {
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [windows.data]);

  // State for dropout risk visibility
  const [dropoutRiskVisibleLines, setDropoutRiskVisibleLines] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Dropout Risk when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(dropoutRiskAssessment.data);
    setDropoutRiskVisibleLines(prev => {
      const newState = { ...prev };
      newState.all = true;
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [dropoutRiskAssessment.data]);

  const toggleDropoutRiskLineVisibility = useCallback((lineKey: string) => {
    setDropoutRiskVisibleLines(prev => {
      const availableIndices = getUniqueIndices(dropoutRiskAssessment.data);
      
      if (availableIndices.length === 1) {
        return prev;
      }
      
      if (lineKey === 'all') {
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[idx] = true;
          });
          return newState;
        } else {
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
          return newState;
        }
      } else {
        const newState = { ...prev };
        newState[lineKey] = !newState[lineKey];
        
        const visibleIndividualLines = availableIndices.filter(idx => newState[idx] === true);
        if (visibleIndividualLines.length === 0) {
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
        } else {
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [dropoutRiskAssessment.data]);

  // State for cross server visibility
  const [crossServerVisibleLines, setCrossServerVisibleLines] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Cross Server when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(crossServerComparison.data);
    setCrossServerVisibleLines(prev => {
      const newState = { ...prev };
      newState.all = true;
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [crossServerComparison.data]);

  const toggleCrossServerLineVisibility = useCallback((lineKey: string) => {
    setCrossServerVisibleLines(prev => {
      const availableIndices = getUniqueIndices(crossServerComparison.data);
      
      if (availableIndices.length === 1) {
        return prev;
      }
      
      if (lineKey === 'all') {
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[idx] = true;
          });
          return newState;
        } else {
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
          return newState;
        }
      } else {
        const newState = { ...prev };
        newState[lineKey] = !newState[lineKey];
        
        const visibleIndividualLines = availableIndices.filter(idx => newState[idx] === true);
        if (visibleIndividualLines.length === 0) {
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
        } else {
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [crossServerComparison.data]);

  // State for cross server metrics visibility
  const [crossServerMetricsVisibleLines, setCrossServerMetricsVisibleLines] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Cross Server Metrics when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(crossServerMetrics.data);
    setCrossServerMetricsVisibleLines(prev => {
      const newState = { ...prev };
      newState.all = true;
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [crossServerMetrics.data]);

  const toggleCrossServerMetricsLineVisibility = useCallback((lineKey: string) => {
    setCrossServerMetricsVisibleLines(prev => {
      const availableIndices = getUniqueIndices(crossServerMetrics.data);
      
      if (availableIndices.length === 1) {
        return prev;
      }
      
      if (lineKey === 'all') {
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[idx] = true;
          });
          return newState;
        } else {
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
          return newState;
        }
      } else {
        const newState = { ...prev };
        newState[lineKey] = !newState[lineKey];
        
        const visibleIndividualLines = availableIndices.filter(idx => newState[idx] === true);
        if (visibleIndividualLines.length === 0) {
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
        } else {
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [crossServerMetrics.data]);

  // State for command security visibility
  const [commandSecurityVisibleLines, setCommandSecurityVisibleLines] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Command Security when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(cmds.data);
    setCommandSecurityVisibleLines(prev => {
      const newState = { ...prev };
      newState.all = true;
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [cmds.data]);

  const toggleCommandSecurityLineVisibility = useCallback((lineKey: string) => {
    setCommandSecurityVisibleLines(prev => {
      const availableIndices = getUniqueIndices(cmds.data);
      
      if (availableIndices.length === 1) {
        return prev;
      }
      
      if (lineKey === 'all') {
        if (prev.all) {
          const newState: Record<string, boolean> = { all: false };
          availableIndices.forEach(idx => {
            newState[idx] = true;
          });
          return newState;
        } else {
          const newState: Record<string, boolean> = { all: true };
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
          return newState;
        }
      } else {
        const newState = { ...prev };
        newState[lineKey] = !newState[lineKey];
        
        const visibleIndividualLines = availableIndices.filter(idx => newState[idx] === true);
        if (visibleIndividualLines.length === 0) {
          newState.all = true;
          availableIndices.forEach(idx => {
            newState[idx] = false;
          });
        } else {
          newState.all = false;
        }
        
        return newState;
      }
    });
  }, [cmds.data]);
  
  // State for command engagement graph visibility - start with all lines visible
  const [commandEngagementVisibleLines, setCommandEngagementVisibleLines] = useState<Record<string, boolean>>({
    'all': true,
    'engagement': true,
    'frequency': true
  });

  // Toggle line visibility - show only selected line
  const toggleLineVisibility = useCallback((lineKey: string) => {
    setVisibleLines(prev => {
      const newState: Record<string, boolean> = {};
      
      // Special handling for "All" option
      if (lineKey === 'all') {
        // Show all lines when "All" is clicked
        // We'll set all possible line keys to true
        Object.keys(prev).forEach(key => {
          newState[key] = true;
        });
        // Also add common line patterns
        const commonPatterns = ['cpu_', 'memory_', 'disk_', 'network_rx_', 'network_tx_'];
        commonPatterns.forEach(pattern => {
          Object.keys(prev).forEach(key => {
            if (key.startsWith(pattern)) {
              newState[key] = true;
            }
          });
        });
        return newState;
      }
      
      // Hide all lines first
      Object.keys(prev).forEach(key => {
        newState[key] = false;
      });
      
      // If the clicked line was already the only visible one, show all
      const wasOnlyVisible = prev[lineKey] === true && Object.values(prev).filter(v => v === true).length === 1;
      
      if (wasOnlyVisible) {
        // Show all lines
        Object.keys(prev).forEach(key => {
          newState[key] = true;
        });
      } else {
        // Show only the clicked line
        newState[lineKey] = true;
      }
      
      return newState;
    });
  }, []);

  // Toggle engagement line visibility
  const toggleEngagementLineVisibility = useCallback((lineKey: string) => {
    setEngagementVisibleLines(prev => {
      const newState: Record<string, boolean> = {};
      
      // Special handling for "All" option
      if (lineKey === 'all') {
        // Show all lines when "All" is clicked
        newState['all'] = true;
        newState['duration'] = true;
        newState['activity'] = true;
      } else {
        // If clicking on a specific line that's already visible, show all
        if (prev[lineKey] === true) {
          newState['all'] = true;
          newState['duration'] = true;
          newState['activity'] = true;
        } else {
          // Show only the clicked line
          newState[lineKey] = true;
        }
      }
      
      return newState;
    });
  }, []);

  // Toggle command engagement line visibility
  const toggleCommandEngagementLineVisibility = useCallback((lineKey: string) => {
    setCommandEngagementVisibleLines(prev => {
      const newState: Record<string, boolean> = {};
      
      // Special handling for "All" option
      if (lineKey === 'all') {
        // Show all lines when "All" is clicked
        newState['all'] = true;
        newState['engagement'] = true;
        newState['frequency'] = true;
      } else {
        // If clicking on a specific line that's already visible, show all
        if (prev[lineKey] === true) {
          newState['all'] = true;
          newState['engagement'] = true;
          newState['frequency'] = true;
        } else {
          // Show only the clicked line
          newState[lineKey] = true;
        }
      }
      
      return newState;
    });
  }, []);

  // Custom Legend component with clickable labels
  const CustomLegend = ({ payload, onToggle, visibilityState }: { payload: any[], onToggle: (key: string) => void, visibilityState?: Record<string, boolean> }) => {
    if (!payload || payload.length === 0) return null;

    // Use provided visibility state or fall back to visibleLines
    const stateToCheck = visibilityState || visibleLines;

    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '16px', marginTop: '16px' }}>
        {payload.map((entry, index) => {
          const lineKey = entry.dataKey || entry.value;
          // Determine if this legend item should appear enabled or disabled
          // Legend items are always visible, but styled based on their state
          let isEnabled = true;
          if (stateToCheck[lineKey] !== undefined) {
            isEnabled = stateToCheck[lineKey] === true;
          } else if (lineKey === 'all') {
            // For 'all', check if any specific items are visible
            isEnabled = Object.values(stateToCheck).some(v => v === true) || Object.keys(stateToCheck).length === 0;
          }
          
          return (
            <div
              key={index}
              onClick={() => onToggle(lineKey)}
              style={{
                display: 'flex',
                alignItems: 'center',
                cursor: 'pointer',
                padding: '4px 8px',
                borderRadius: '4px',
                backgroundColor: isEnabled ? 'transparent' : '#f0f0f0',
                opacity: isEnabled ? 1 : 0.5,
                transition: 'all 0.2s ease',
                border: isEnabled ? '1px solid transparent' : '1px solid #ddd'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = isEnabled ? '#f8f8f8' : '#e8e8e8';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = isEnabled ? 'transparent' : '#f0f0f0';
              }}
            >
              <div
                style={{
                  width: '12px',
                  height: '12px',
                  backgroundColor: isEnabled ? entry.color : '#ccc',
                  marginRight: '8px',
                  borderRadius: '2px'
                }}
              />
              <span style={{ fontSize: '12px', color: isEnabled ? '#333' : '#999' }}>
                {entry.value}
              </span>
            </div>
          );
        })}
      </div>
    );
  };

  // Helper function to create legend payload for multi-index charts
  const createLegendPayload = useCallback((indices: string[], metric: string, colors: string[]) => {
    const payload = [
      // Add "All" option at the beginning
      {
        value: `All ${metric}`,
        dataKey: 'all',
        color: '#333333'
      },
      // Add individual index options
      ...indices.map((idx, index) => {
        // Map metric names to their corresponding dataKey prefixes
        const metricMap: Record<string, string> = {
          'CPU %': 'cpu',
          'Memory %': 'memory', 
          'Disk GB': 'disk',
          'RX MB': 'network_rx',
          'TX MB': 'network_tx'
        };
        
        const baseMetric = metricMap[metric] || metric.toLowerCase().replace(/[^a-z]/g, '');
        const dataKey = `${baseMetric}_${idx}`;
        
        return {
          value: `${metric} (${idx})`,
          dataKey: dataKey,
          color: colors[index % colors.length]
        };
      })
    ];
    return payload;
  }, []);

  // Get unique indices from data
  const getUniqueIndices = useCallback((data: any[]) => {
    const indices = [...new Set(data.map(d => d.sourceIndex).filter(Boolean))];
    return indices;
  }, []);

  // Helper function to create legend payload for engagement charts
  const createEngagementLegendPayload = useCallback((indices: string[], metric: string, colors: string[]) => {
    const payload = [
      // Add "All" option at the beginning
      {
        value: `All ${metric}`,
        dataKey: 'all',
        color: '#8884d8'
      },
      // Add individual index options
      ...indices.map((idx, index) => {
        // Map metric names to their corresponding dataKey prefixes
        const metricMap: Record<string, string> = {
          'Duration': 'duration',
          'Activity': 'activity'
        };
        
        const baseMetric = metricMap[metric] || metric.toLowerCase().replace(/[^a-z]/g, '');
        const dataKey = `${baseMetric}_${idx}`;
        
        return {
          value: `${metric} (${idx})`,
          dataKey: dataKey,
          color: colors[index % colors.length]
        };
      })
    ];
    
    return payload;
  }, []);

  // Helper function to create legend payload for command engagement charts
  const createCommandEngagementLegendPayload = useCallback((indices: string[], metric: string, colors: string[]) => {
    const payload = [
      // Add "All" option at the beginning
      {
        value: `All`,
        dataKey: 'all',
        color: '#8884d8'
      }
    ];
    
    // Add individual index options (just show index name without metric)
    indices.forEach((index, idxIndex) => {
      payload.push({
        value: index,
        dataKey: `${metric.toLowerCase()}_${index}`,
        color: colors[idxIndex]
      });
    });
    
    return payload;
  }, []);

  // Unique indices extractor for command engagement data (keys like engagement_<index>)
  const getUniqueIndicesFromCommandData = useCallback((data: any[]) => {
    const unique = new Set<string>();
    for (const row of data) {
      for (const key of Object.keys(row || {})) {
        if (key.startsWith('engagement_')) {
          unique.add(key.substring('engagement_'.length));
        }
        if (key.startsWith('frequency_')) {
          unique.add(key.substring('frequency_'.length));
        }
      }
    }
    return Array.from(unique);
  }, []);

  const formatXAxisTick = (tickItem: string, index: number, data: any[]) => {
    // Show every 5th tick to match overview tab frequency
    if (index % 5 !== 0) {
      return '';
    }
    
    // If tickItem is a valid date, format it
    const date = new Date(tickItem);
    
    if (!isNaN(date.getTime())) {
      // Always show both date and time for now to test
      const formatted = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
      return formatted;
    } else {
      // Fallback to showing data point number
      return `Point ${index + 1}`;
    }
  };

  // Processed data with index-specific fields for multi-index visualization
  const perfData = useMemo(() => {
    if (perf.data.length === 0) {
      return [];
    }
    
    const processedData = perf.data.map((d: PerfDoc, index) => {
      // Try different timestamp field names
      const timestamp = d.timestamp || (d as any).time || (d as any).date || (d as any).created_at || (d as any).ts;
      
      // Process the record data
      
      let date: Date;
      
      if (!timestamp) {
        // Generate sequential time points based on index
        const baseTime = new Date();
        date = new Date(baseTime.getTime() + (index * 60000)); // 1 minute intervals
      } else {
        date = new Date(timestamp);
        // Check if date is valid
        if (isNaN(date.getTime())) {
          const baseTime = new Date();
          date = new Date(baseTime.getTime() + (index * 60000));
        }
      }
      
      const sourceIndex = (d as any).sourceIndex || 'unknown';
      
      return {
        ts: date.toLocaleTimeString(),
        dateTime: date.toLocaleString(),
        date: date.toLocaleDateString(),
        time: date.toLocaleTimeString(),
        index: index, // Add index as fallback
        sourceIndex: sourceIndex, // Add source index for color coding
        cpu: d.data?.cpu?.utilization_percent || 0,
        memory: d.data?.memory?.ram_percent || 0,
        disk: ((d.data?.disk?.io_read_bytes || 0) + (d.data?.disk?.io_write_bytes || 0)) / (1024 * 1024 * 1024),
        network_rx: (d.data?.network?.bytes_recv || 0) / (1024 * 1024), // RX in MB
        network_tx: (d.data?.network?.bytes_sent || 0) / (1024 * 1024), // TX in MB
        network: ((d.data?.network?.bytes_sent || 0) + (d.data?.network?.bytes_recv || 0)) / (1024 * 1024), // Keep total for backward compatibility
        // Add index-specific CPU fields for multi-index visualization
        [`cpu_${sourceIndex}`]: d.data?.cpu?.utilization_percent || 0,
        [`memory_${sourceIndex}`]: d.data?.memory?.ram_percent || 0,
        [`disk_${sourceIndex}`]: ((d.data?.disk?.io_read_bytes || 0) + (d.data?.disk?.io_write_bytes || 0)) / (1024 * 1024 * 1024),
        [`network_rx_${sourceIndex}`]: (d.data?.network?.bytes_recv || 0) / (1024 * 1024),
        [`network_tx_${sourceIndex}`]: (d.data?.network?.bytes_sent || 0) / (1024 * 1024)
      };
    });
    
    // Sort processed data by timestamp to ensure continuous lines
    processedData.sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime());
    
    return processedData;
  }, [perf.data]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'engagement', label: 'Engagement Analytics', icon: '🎯' },
    { id: 'learning', label: 'Learning & Skills', icon: '🧠' },
    { id: 'usage', label: 'Usage Patterns', icon: '📱' },
    { id: 'risk', label: 'Risk Assessment', icon: '⚠️' },
    { id: 'comparison', label: 'Cross-Server Analysis', icon: '🔄' },
    { id: 'security', label: 'Security & Risk', icon: '🔒' },
    { id: 'analytics', label: 'Advanced Analytics', icon: '📈' },
    { id: 'developer', label: 'Developer Insights', icon: '💻' }
  ];

  // Processed data for different tabs
  const engagementData = useMemo(() => {
    
    // Check if all data has zero values and add sample data if needed
    const hasValidData = engagementSessions.data.some(d => {
      const data = d.data as any;
      
      // Calculate duration from timestamps
      let duration = 0;
      if (data && data.start_time) {
        const startTime = new Date(data.start_time);
        const endTime = new Date(d.timestamp);
        if (!isNaN(startTime.getTime()) && !isNaN(endTime.getTime())) {
          duration = Math.max(0, Math.floor((endTime.getTime() - startTime.getTime()) / (1000 * 60)));
        }
      }
      
      return duration > 0; // If we can calculate a meaningful duration, we have valid data
    });
    
    if (!hasValidData) {
      return [];
    }
    
    const processedData = engagementSessions.data.map(d => {
      const date = new Date(d.timestamp);
      
      // Calculate duration from start_time and current timestamp
      const data = d.data as any;
      let duration = 0;
      let activity = 0;
      
      if (data.start_time) {
        const startTime = new Date(data.start_time);
        const endTime = new Date(d.timestamp);
        duration = Math.max(0, Math.floor((endTime.getTime() - startTime.getTime()) / (1000 * 60))); // Convert to minutes
      }
      
      // For activity, we'll use a calculated value based on session duration
      // This is a reasonable approximation since we don't have actual activity data
      activity = Math.floor(duration * 0.5);
      
      // Create index-specific data keys like in overview tab
      const indexName = (d as any).sourceIndex || 'unknown';
      const baseData: any = {
        ts: date.toLocaleTimeString(),
        dateTime: date.toLocaleString(),
        date: date.toLocaleDateString(),
        time: date.toLocaleTimeString(),
        sourceIndex: indexName,
      };
      
      // Add index-specific keys for duration and activity
      baseData[`duration_${indexName}`] = duration;
      baseData[`activity_${indexName}`] = activity;
      
      return baseData;
    });
    
    return processedData;
  }, [engagementSessions.data]);

  const skillData = useMemo(() => {
    return learningProgress.data.map(d => ({
      skill: d.data.skill || 'Unknown',
      progress: d.data.progress_percent || 0,
      level: d.data.level || 'Beginner',
    }));
  }, [learningProgress.data]);

  const appUsageData = useMemo(() => {
    return appUsageStats.data.map(d => ({
      app: d.data.app_name || 'Unknown',
      usage: d.data.usage_minutes || 0,
      category: d.data.category || 'Other',
    }));
  }, [appUsageStats.data]);

  const dailyActivityData = useMemo(() => {
    return dailyActivity.data.map(d => ({
      date: d.data.date || new Date(d.timestamp).toLocaleDateString(),
      hours: d.data.total_hours || 0,
      productivity: d.data.productivity_score || 0,
    }));
  }, [dailyActivity.data]);

  const securityData = useMemo(() => {
    return dropoutRiskAssessment.data.map((d: any) => ({
      user: d.data?.user_id || 'Unknown',
      risk: d.data?.risk_score || 0,
      factors: d.data?.risk_factors?.length || 0,
      sessions: d.data?.session_count || 0,
    }));
  }, [dropoutRiskAssessment.data]);

  // New processed data for additional analytics
  const commandEngagementData = useMemo(() => {
    if (commandEngagement.data.length === 0) {
      return [];
    }

    // Extract commands with index-specific tracking
    const commandCounts: Record<string, Record<string, { count: number; engagement: number }>> = {};

    const addCommand = (commandRaw: any, sourceIndex: string, countInc: number = 1) => {
      const key = typeof commandRaw === 'string' ? commandRaw : (commandRaw?.command || commandRaw?.name || commandRaw?.text || 'Unknown');
      const normalized = (key || 'Unknown').toString().trim().toLowerCase();
      if (!normalized) return;
      if (!commandCounts[normalized]) commandCounts[normalized] = {};
      if (!commandCounts[normalized][sourceIndex]) commandCounts[normalized][sourceIndex] = { count: 0, engagement: 0 };
      commandCounts[normalized][sourceIndex].count += countInc;
      // Simple engagement heuristic: complexity by length, capped 1..10, scaled by count
      const score = Math.min(10, Math.max(1, normalized.length * 0.5));
      commandCounts[normalized][sourceIndex].engagement += score * countInc;
    };

    for (const record of commandEngagement.data) {
      // Support multiple shapes: data.command_monitoring in monitoring_summary, data.summary, data, summary, or root
      const root: any = record as any;
      const monitoring = root?.data?.command_monitoring || {};
      const summary = (root?.data?.summary) || (root?.data) || (root?.summary) || root || {};
      const sourceIndex = (record as any).sourceIndex || 'unknown';

      // recent_commands: array<string|obj>
      if (Array.isArray(summary.recent_commands)) {
        for (const cmd of summary.recent_commands) addCommand(cmd, sourceIndex, 1);
      }

      // command_patterns: { command: count }
      if (summary.command_patterns && typeof summary.command_patterns === 'object') {
        for (const [command, count] of Object.entries(summary.command_patterns)) addCommand(command, sourceIndex, Number(count) || 1);
      }

      // top_commands: array<{command,count}>
      if (Array.isArray(summary.top_commands)) {
        for (const item of summary.top_commands) addCommand((item as any)?.command, sourceIndex, Number((item as any)?.count) || 1);
      }

      // commands: array<string>
      if (Array.isArray(summary.commands)) {
        for (const cmd of summary.commands) addCommand(cmd, sourceIndex, 1);
      }

      // monitoring_summary.command_monitoring.recent_alerts[].command
      if (Array.isArray(monitoring.recent_alerts)) {
        for (const alert of monitoring.recent_alerts) {
          if ((alert as any)?.command) addCommand((alert as any).command, sourceIndex, 1);
        }
      }

      // monitoring_summary.command_monitoring.command_patterns may be categorized; flatten values if numbers
      if (monitoring.command_patterns && typeof monitoring.command_patterns === 'object') {
        // If it's already command:count, add directly
        for (const [k, v] of Object.entries(monitoring.command_patterns)) {
          const num = Number(v);
          if (!Number.isNaN(num)) addCommand(k, sourceIndex, num || 1);
        }
      }

      // direct fields
      if ((record as any).command) addCommand((record as any).command, sourceIndex, 1);
      if (summary.command) addCommand(summary.command, sourceIndex, 1);
      if (summary.cmd) addCommand(summary.cmd, sourceIndex, 1);
      if (summary.command_text) addCommand(summary.command_text, sourceIndex, 1);
      if (summary.text) addCommand(summary.text, sourceIndex, 1);
      if (summary.name) addCommand(summary.name, sourceIndex, 1);
    }

    // Convert to array format for the chart with all indexes
    const processed = Object.entries(commandCounts)
      .map(([command, indexData]) => {
        const baseData: any = { command };
        Object.entries(indexData).forEach(([index, info]) => {
          baseData[`engagement_${index}`] = Math.round(info.engagement / Math.max(1, info.count));
          baseData[`frequency_${index}`] = info.count;
        });
        return baseData;
      })
      .sort((a, b) => {
        // Sort by total engagement across all indexes
        const sumEng = (obj: any) => Object.keys(obj).filter(k => k.startsWith('engagement_')).reduce((s, k) => s + (Number(obj[k]) || 0), 0);
        return sumEng(b) - sumEng(a);
      })
      .slice(0, 15);

    return processed;
  }, [commandEngagement.data]);

  // New: Build command pattern category data from monitoring_summary.command_monitoring.command_patterns
  const commandPatternData = useMemo(() => {
      if (commandEngagement.data.length === 0) {
        return [];
      }

    const byCategory: Record<string, any> = {};

    for (const rec of commandEngagement.data) {
      const root: any = rec as any;
      const idx = (root?.sourceIndex) || (root?._index) || 'unknown';
      // Try multiple paths for command_patterns
      const cm = root?.data?.command_monitoring || root?.command_monitoring || root?.data;
      const patterns = cm?.command_patterns;

      if (!patterns || typeof patterns !== 'object') continue;

      for (const [category, value] of Object.entries(patterns)) {
        const count = Number(value) || 0;

        if (count <= 0) continue;

        if (!byCategory[category]) {
          byCategory[category] = { category };
        }

        byCategory[category][`count_${idx}`] = (byCategory[category][`count_${idx}`] || 0) + count;
      }
    }

    const result = Object.values(byCategory);
    return result;
  }, [commandEngagement.data]);

  // Helper to extract indices from commandPatternData
  const getIndicesFromPatternData = useCallback((data: any[]) => {
    const s = new Set<string>();
    for (const row of data) {
      Object.keys(row).forEach(k => { if (k.startsWith('count_')) s.add(k.substring('count_'.length)); });
    }
    return Array.from(s);
  }, []);

  // Helper to extract indices from Top Commands data
  const getIndicesFromTopCommandsData = useCallback((data: any[]) => {
    const s = new Set<string>();
    for (const row of data) {
      Object.keys(row).forEach(k => { if (k.startsWith('count_')) s.add(k.substring('count_'.length)); });
    }
    return Array.from(s);
  }, []);

  // Helper to log and return true
  const debugLog = (message: string) => {
    console.log(message);
    return true;
  };

  // Fallback: Aggregate engagement by index (monitoring_summary.command_monitoring)
  const commandEngagementIndexData = useMemo(() => {
    if (commandEngagement.data.length === 0) {
      return [];
    }

    const byIndex: Record<string, { index: string; total: number; dangerous: number; alerts: number }> = {};

    for (const record of commandEngagement.data) {
      const root: any = record as any;
      const idx = (root?.sourceIndex) || (root?._index) || 'unknown';
      // Try multiple paths for command_monitoring data
      const cm = root?.data?.command_monitoring || root?.command_monitoring || root?.data;

      if (!cm) continue;

      if (!byIndex[idx]) {
        byIndex[idx] = { index: idx, total: 0, dangerous: 0, alerts: 0 };
      }

      const total = Number(cm.total_commands) || Number(cm?.security_metrics?.total_commands) || 0;
      const dangerous = Number(cm?.security_metrics?.dangerous_commands) || 0;
      const alerts = Array.isArray(cm.recent_alerts) ? cm.recent_alerts.length : 0;

      byIndex[idx].total += total;
      byIndex[idx].dangerous += dangerous;
      byIndex[idx].alerts += alerts;
    }

    const result = Object.values(byIndex);
    return result;
  }, [commandEngagement.data]);

  // Visibility for index-level engagement bars
  const [commandIndexVisibleBars, setCommandIndexVisibleBars] = useState<Record<string, boolean>>({
    all: true,
    total: true,
    dangerous: true,
    alerts: true,
  });

  // Visibility for Top Commands bars per index
  const [topCommandsVisibleBars, setTopCommandsVisibleBars] = useState<Record<string, boolean>>({
    all: true,
  });

  // Initialize visibility state for Top Commands when data changes
  useEffect(() => {
    const availableIndices = getUniqueIndices(cmds.data);
    setTopCommandsVisibleBars(prev => {
      const newState = { ...prev };
      // Always ensure 'all' is true by default
      newState.all = true;
      // Ensure all indices are visible by default
      availableIndices.forEach(idx => {
        newState[idx] = true;
      });
      return newState;
    });
  }, [cmds.data]);

  // Additional initialization on component mount
  useEffect(() => {
    setTopCommandsVisibleBars(prev => ({
      ...prev,
      all: true
    }));
  }, []);

  const toggleTopCommandsBarVisibility = useCallback((barKey: string) => {
    setTopCommandsVisibleBars(prev => {
      const availableIndices = getUniqueIndices(cmds.data);
      
      // If only one index, no need for complex toggle logic
      if (availableIndices.length === 1) {
        return prev; // No change needed for single index
      }
      
      const newState: Record<string, boolean> = {};
      
      // Special handling for "All" option
      if (barKey === 'all') {
        // Show all bars when "All" is clicked
        Object.keys(prev).forEach(key => {
          newState[key] = true;
        });
        // Also add common bar patterns for indices
        availableIndices.forEach(index => {
          newState[`count_${index}`] = true;
        });
        return newState;
      }
      
      // Hide all lines first
      Object.keys(prev).forEach(key => {
        newState[key] = false;
      });
      
      // If the clicked bar was already the only visible one, show all
      const wasOnlyVisible = prev[barKey] === true && Object.values(prev).filter(v => v === true).length === 1;
      
      if (wasOnlyVisible) {
        // Show all bars
        Object.keys(prev).forEach(key => {
          newState[key] = true;
        });
      } else {
        // Show only the clicked bar
        newState[barKey] = true;
      }
      
      return newState;
    });
  }, [cmds.data]);

  const toggleCommandIndexBarVisibility = useCallback((key: string) => {
    setCommandIndexVisibleBars(prev => {
      const next: Record<string, boolean> = {};
      if (key === 'all' || prev[key]) {
        next.all = true; next.total = true; next.dangerous = true; next.alerts = true;
      } else {
        next[key] = true;
      }
      return next;
    });
  }, []);

  const skillAnalyticsData = useMemo(() => {
    return skillProgressAnalytics.data.map((d: any) => ({
      skill: d.data?.skill || 'Unknown',
      proficiency: d.data?.proficiency_score || 0,
      confidence: d.data?.confidence_level || 0,
      trend: d.data?.trend_direction || 'stable',
    }));
  }, [skillProgressAnalytics.data]);

  const skillComparisonData = useMemo(() => {
    return skillCrossComparison.data.map((d: any) => ({
      skill: d.data?.skill || 'Unknown',
      server: d.data?.server_id || 'Unknown',
      progress: d.data?.progress_percent || 0,
      rank: d.data?.rank || 0,
    }));
  }, [skillCrossComparison.data]);

  const dropoutRiskData = useMemo(() => {
    return dropoutRiskAssessment.data.map((d: any) => ({
      user: d.data?.user_id || 'Unknown',
      riskScore: d.data?.risk_score || 0,
      factors: d.data?.risk_factors || [],
      prediction: d.data?.dropout_prediction || 'low',
    }));
  }, [dropoutRiskAssessment.data]);

  const crossServerMetricsData = useMemo(() => {
    return crossServerMetrics.data.map((d: any) => ({
      server: d.data?.server_id || 'Unknown',
      metric: d.data?.metric_name || 'Unknown',
      value: d.data?.value || 0,
      timestamp: d.timestamp,
    }));
  }, [crossServerMetrics.data]);

  const crossServerComparisonData = useMemo(() => {
    return crossServerComparison.data.map((d: any) => ({
      server: d.data?.server_id || 'Unknown',
      comparison: d.data?.comparison_metric || 'Unknown',
      value: d.data?.value || 0,
      percentile: d.data?.percentile || 0,
    }));
  }, [crossServerComparison.data]);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview': return (
        <div>
          <h3>Commands</h3>
          {cmds.data.length === 0 ? (
            <NoDataMessage message="No command data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={(() => {
              // Extract commands from the correct data structure with multi-index support
              const commandCounts: Record<string, Record<string, { count: number; dangerous: boolean }>> = {};
              
              for (const record of cmds.data) {
                const root: any = record as any;
                const data = root?.data || {};
                const sourceIndex = (root as any).sourceIndex || 'unknown';
                
                // Check for command_monitoring data structure - it's in data.command_monitoring
                const commandMonitoring = data?.command_monitoring || {};
                
                // Extract from recent_alerts[].command (individual commands)
                if (Array.isArray(commandMonitoring.recent_alerts)) {
                  for (const alert of commandMonitoring.recent_alerts) {
                    const command = alert?.command;
                    if (command && typeof command === 'string') {
                      // Use the full command instead of just the base name
                      const fullCommand = command.trim();
                      
                      if (!commandCounts[fullCommand]) {
                        commandCounts[fullCommand] = {};
                      }
                      if (!commandCounts[fullCommand][sourceIndex]) {
                        commandCounts[fullCommand][sourceIndex] = { count: 0, dangerous: false };
                      }
                      commandCounts[fullCommand][sourceIndex].count += 1;
                      // Mark as dangerous if risk_level is high/critical
                      if (alert?.risk_level === 'high' || alert?.risk_level === 'critical') {
                        commandCounts[fullCommand][sourceIndex].dangerous = true;
                      }
                    }
                  }
                }
                
                // Also check for command_patterns (category counts) as fallback
                if (commandMonitoring.command_patterns && typeof commandMonitoring.command_patterns === 'object') {
                  for (const [command, count] of Object.entries(commandMonitoring.command_patterns)) {
                    const normalized = (command as string).trim().toLowerCase();
                    if (!commandCounts[normalized]) {
                      commandCounts[normalized] = {};
                    }
                    if (!commandCounts[normalized][sourceIndex]) {
                      commandCounts[normalized][sourceIndex] = { count: 0, dangerous: false };
                    }
                    commandCounts[normalized][sourceIndex].count += Number(count) || 0;
                  }
                }
                
                // Check for recent_commands directly in data (if it exists)
                if (Array.isArray(commandMonitoring.recent_commands)) {
                  for (const cmd of commandMonitoring.recent_commands) {
                    const key = typeof cmd === 'string' ? cmd : (cmd?.command || 'Unknown');
                    const normalized = key.trim().toLowerCase();
                    if (!commandCounts[normalized]) {
                      commandCounts[normalized] = {};
                    }
                    if (!commandCounts[normalized][sourceIndex]) {
                      commandCounts[normalized][sourceIndex] = { count: 0, dangerous: false };
                    }
                    commandCounts[normalized][sourceIndex].count += 1;
                  }
                }
                
              }
              
              // Transform to multi-index structure like other graphs
              const processed = Object.entries(commandCounts).map(([command, indexData]) => {
                const baseData: any = { command: command };
                let totalCount = 0;
                let isDangerous = false;
                
                Object.entries(indexData).forEach(([index, info]) => {
                  baseData[`count_${index}`] = info.count;
                  baseData[`dangerous_${index}`] = info.dangerous ? 1 : 0;
                  totalCount += info.count;
                  if (info.dangerous) isDangerous = true;
                });
                
                baseData.totalCount = totalCount;
                baseData.isDangerous = isDangerous;
                return baseData;
              })
              .sort((a, b) => b.totalCount - a.totalCount)
              .slice(0, 10); // Top 10 commands
              
              return processed;
            })()}>
          <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="command"
                interval="preserveStartEnd"
                angle={-45}
                textAnchor="end"
                height={80}
                tick={{ fontSize: 10 }}
                tickFormatter={(value) => {
                  // Truncate long commands for display
                  if (value.length > 40) {
                    return value.substring(0, 37) + '...';
                  }
                  return value;
                }}
              />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [value, name === 'dangerous' ? 'Dangerous' : 'Count']}
                labelFormatter={(label) => `Command: ${label}`}
                labelStyle={{ maxWidth: '300px', whiteSpace: 'normal', wordWrap: 'break-word' }}
              />
              <Legend 
                content={() => {
                  // Extract indices from available data  
                  const availableIndices = getUniqueIndices(cmds.data);
                  const colors = availableIndices.map((_, i) => getIndexColor(availableIndices[i], i));
                  
                  // Calculate total commands across all indices
                  let totalCommands = 0;
                  const indexCommandCounts: Record<string, number> = {};
                  
                  // Process command data to get counts per index
                  const commandCounts: Record<string, Record<string, { count: number; dangerous: boolean }>> = {};
                  
                  for (const record of cmds.data) {
                    const root: any = record as any;
                    const data = root?.data || {};
                    const sourceIndex = (root as any).sourceIndex || 'unknown';
                    
                    const commandMonitoring = data?.command_monitoring || {};
                    
                    // Extract from recent_alerts[].command (individual commands)
                    if (Array.isArray(commandMonitoring.recent_alerts)) {
                      for (const alert of commandMonitoring.recent_alerts) {
                        const command = alert?.command;
                        if (command && typeof command === 'string') {
                          const fullCommand = command.trim();
                          
                          if (!commandCounts[fullCommand]) {
                            commandCounts[fullCommand] = {};
                          }
                          if (!commandCounts[fullCommand][sourceIndex]) {
                            commandCounts[fullCommand][sourceIndex] = { count: 0, dangerous: false };
                          }
                          commandCounts[fullCommand][sourceIndex].count += 1;
                          commandCounts[fullCommand][sourceIndex].dangerous = commandCounts[fullCommand][sourceIndex].dangerous || (alert?.risk_score > 0.5);
                        }
                      }
                    }
                  }
                  
                  // Calculate counts per index
                  availableIndices.forEach(index => {
                    let indexCount = 0;
                    Object.values(commandCounts).forEach(commandData => {
                      if (commandData[index]) {
                        indexCount += commandData[index].count;
                      }
                    });
                    indexCommandCounts[index] = indexCount;
                    totalCommands += indexCount;
                  });
                  
                  // Create payload with counts
                  const payload = availableIndices.length > 1 
                    ? [
                        { value: `All Commands (${totalCommands})`, dataKey: 'all', color: '#8884d8' },
                        ...availableIndices.map((idx, i) => ({ 
                          value: `${idx} (${indexCommandCounts[idx] || 0})`, 
                          dataKey: `count_${idx}`, 
                          color: colors[i] 
                        }))
                      ]
                    : availableIndices.map((idx, i) => ({ 
                        value: `${idx} (${indexCommandCounts[idx] || 0})`, 
                        dataKey: `count_${idx}`, 
                        color: colors[i] 
                      }));
                  
                  return <CustomLegend payload={payload} onToggle={toggleTopCommandsBarVisibility} visibilityState={topCommandsVisibleBars} />;
                }}
              />
              {getUniqueIndices(cmds.data).map((idx, i) => {
                const barKey = `count_${idx}`;
                const availableIndices = getUniqueIndices(cmds.data);
                
                // If only one index, always show it
                if (availableIndices.length === 1) {
                  return <Bar key={idx} dataKey={barKey} name={idx} fill={getIndexColor(idx, i)} />;
                }
                
                // For multiple indices, use same visibility logic as other graphs
                const isVisible = topCommandsVisibleBars[barKey] === true || 
                                 (topCommandsVisibleBars[barKey] === undefined && Object.keys(topCommandsVisibleBars).length === 0) || 
                                 topCommandsVisibleBars['all'] === true;
                
                return isVisible ? (
                  <Bar key={idx} dataKey={barKey} name={idx} fill={getIndexColor(idx, i)} />
                ) : null;
              })}
            </BarChart>
          </ResponsiveContainer>
          )}

          <h3>CPU Usage</h3>
          {perfData.length === 0 ? (
            <NoDataMessage message="No CPU data available for the selected time range. Try adjusting the date filter or selecting a different time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={perfData}>
          <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="dateTime"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={100}
                tickFormatter={(value, index) => {
                  // Only show every 5th tick to reduce clutter
                  if (index % 5 !== 0) {
                    return '';
                  }
                  
                  // Parse the dateTime value
                  const date = new Date(value);
                  
                  // Check if date is valid
                  if (!isNaN(date.getTime())) {
                    // For multi-day ranges, show date + time
                    // For single-day ranges, show time only
                    if (perfData.length > 0) {
                      const firstDate = new Date(perfData[0].dateTime);
                      const lastDate = new Date(perfData[perfData.length - 1].dateTime);
                      
                      // Check if data spans different calendar days
                      const firstDay = firstDate.toLocaleDateString();
                      const lastDay = lastDate.toLocaleDateString();
                      const spansMultipleDays = firstDay !== lastDay;
                      
                      if (spansMultipleDays) {
                        // Multi-day: show date + time
                        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                      } else {
                        // Single day: show time only
                        return date.toLocaleTimeString();
                      }
                    }
                    // Fallback: show date + time
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                  } else {
                    // Fallback if date parsing fails
                    return `Point ${index + 1}`;
                  }
                }}
              />
              <YAxis />
          <Tooltip />
              <Legend 
                content={(props) => {
                  if (index === 'all') {
                    if (!perfData || perfData.length === 0) {
                      return <CustomLegend payload={[{ value: 'CPU %', dataKey: 'cpu', color: '#8884d8' }]} onToggle={toggleLineVisibility} />;
                    }
                    const indices = getUniqueIndices(perfData);
                    const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                    const payload = createLegendPayload(indices, 'CPU %', colors);
                    return <CustomLegend payload={payload} onToggle={toggleLineVisibility} />;
                  }
                  return <CustomLegend payload={[{ value: 'CPU %', dataKey: 'cpu', color: '#8884d8' }]} onToggle={toggleLineVisibility} />;
                }}
              />
              {index === 'all' && perfData && perfData.length > 0 ? (
                // Show separate lines for each index when "All" is selected
                getUniqueIndices(perfData).map((idx, idxIndex) => {
                  const lineKey = `cpu_${idx}`;
                  const isVisible = visibleLines[lineKey] === true || (visibleLines[lineKey] === undefined && Object.keys(visibleLines).length === 0) || visibleLines['all'] === true;
                  
                  // Only render the line if it's visible
                  if (!isVisible) return null;
                  
                  return (
                    <Line 
                      key={`cpu-${idx}`}
                      type="monotone" 
                      dataKey={`cpu_${idx}`}
                      stroke={getIndexColor(idx, idxIndex)} 
                      name={`CPU % (${idx})`}
                      connectNulls={true}
                      dot={false}
                      strokeWidth={2}
                    />
                  );
                })
              ) : (
                // Show single line when specific index is selected
                <Line type="monotone" dataKey="cpu" stroke="#8884d8" name="CPU %" strokeWidth={2} connectNulls={true} dot={false} />
              )}
        </LineChart>
      </ResponsiveContainer>
          )}

          <h3>Memory Usage</h3>
          {perfData.length === 0 ? (
            <NoDataMessage message="No Memory data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={perfData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="dateTime"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={100}
                tickFormatter={(value, index) => {
                  // Only show every 5th tick to reduce clutter
                  if (index % 5 !== 0) {
                    return '';
                  }
                  
                  // Parse the dateTime value
                  const date = new Date(value);
                  
                  // Check if date is valid
                  if (!isNaN(date.getTime())) {
                    // For multi-day ranges, show date + time
                    // For single-day ranges, show time only
                    if (perfData.length > 0) {
                      const firstDate = new Date(perfData[0].dateTime);
                      const lastDate = new Date(perfData[perfData.length - 1].dateTime);
                      // Check if data spans different calendar days
                      const firstDay = firstDate.toLocaleDateString();
                      const lastDay = lastDate.toLocaleDateString();
                      const spansMultipleDays = firstDay !== lastDay;
                      
                      if (spansMultipleDays) {
                        // Multi-day: show date + time
                        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                      } else {
                        // Single day: show time only
                        return date.toLocaleTimeString();
                      }
                    }
                    // Fallback: show date + time
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                  } else {
                    // Fallback if date parsing fails
                    return `Point ${index + 1}`;
                  }
                }}
              />
              <YAxis />
              <Tooltip />
              <Legend 
                content={(props) => {
                  if (index === 'all') {
                    if (!perfData || perfData.length === 0) {
                      return <CustomLegend payload={[{ value: 'Memory %', dataKey: 'memory', color: '#82ca9d' }]} onToggle={toggleLineVisibility} />;
                    }
                    const indices = getUniqueIndices(perfData);
                    const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                    const payload = createLegendPayload(indices, 'Memory %', colors);
                    return <CustomLegend payload={payload} onToggle={toggleLineVisibility} />;
                  }
                  return <CustomLegend payload={[{ value: 'Memory %', dataKey: 'memory', color: '#82ca9d' }]} onToggle={toggleLineVisibility} />;
                }}
              />
              {index === 'all' && perfData && perfData.length > 0 ? (
                // Show separate lines for each index when "All" is selected
                getUniqueIndices(perfData).map((idx, idxIndex) => {
                  const lineKey = `memory_${idx}`;
                  const isVisible = visibleLines[lineKey] === true || (visibleLines[lineKey] === undefined && Object.keys(visibleLines).length === 0) || visibleLines['all'] === true;
                  
                  // Only render the line if it's visible
                  if (!isVisible) return null;
                  
                  return (
                    <Line 
                      key={`memory-${idx}`}
                      type="monotone" 
                      dataKey={`memory_${idx}`}
                      stroke={getIndexColor(idx, idxIndex)} 
                      name={`Memory % (${idx})`}
                      connectNulls={true}
                      dot={false}
                      strokeWidth={2}
                    />
                  );
                })
              ) : (
                // Show single line when specific index is selected
                <Line type="monotone" dataKey="memory" stroke="#82ca9d" name="Memory %" strokeWidth={2} connectNulls={true} dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
          )}

          <h3>Disk Usage</h3>
          {perfData.length === 0 ? (
            <NoDataMessage message="No Disk data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={perfData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="dateTime"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={100}
                tickFormatter={(value, index) => {
                  // Only show every 5th tick to reduce clutter
                  if (index % 5 !== 0) {
                    return '';
                  }
                  
                  // Parse the dateTime value
                  const date = new Date(value);
                  
                  // Check if date is valid
                  if (!isNaN(date.getTime())) {
                    // For multi-day ranges, show date + time
                    // For single-day ranges, show time only
                    if (perfData.length > 0) {
                      const firstDate = new Date(perfData[0].dateTime);
                      const lastDate = new Date(perfData[perfData.length - 1].dateTime);
                      // Check if data spans different calendar days
                      const firstDay = firstDate.toLocaleDateString();
                      const lastDay = lastDate.toLocaleDateString();
                      const spansMultipleDays = firstDay !== lastDay;
                      
                      if (spansMultipleDays) {
                        // Multi-day: show date + time
                        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                      } else {
                        // Single day: show time only
                        return date.toLocaleTimeString();
                      }
                    }
                    // Fallback: show date + time
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                  } else {
                    // Fallback if date parsing fails
                    return `Point ${index + 1}`;
                  }
                }}
              />
              <YAxis />
              <Tooltip />
              <Legend 
                content={(props) => {
                  if (index === 'all') {
                    if (!perfData || perfData.length === 0) {
                      return <CustomLegend payload={[{ value: 'Disk GB', dataKey: 'disk', color: '#ffc658' }]} onToggle={toggleLineVisibility} />;
                    }
                    const indices = getUniqueIndices(perfData);
                    const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                    const payload = createLegendPayload(indices, 'Disk GB', colors);
                    return <CustomLegend payload={payload} onToggle={toggleLineVisibility} />;
                  }
                  return <CustomLegend payload={[{ value: 'Disk GB', dataKey: 'disk', color: '#ffc658' }]} onToggle={toggleLineVisibility} />;
                }}
              />
              {index === 'all' && perfData && perfData.length > 0 ? (
                // Show separate lines for each index when "All" is selected
                getUniqueIndices(perfData).map((idx, idxIndex) => {
                  const lineKey = `disk_${idx}`;
                  const isVisible = visibleLines[lineKey] === true || (visibleLines[lineKey] === undefined && Object.keys(visibleLines).length === 0) || visibleLines['all'] === true;
                  
                  // Only render the line if it's visible
                  if (!isVisible) return null;
                  
                  return (
                    <Line 
                      key={`disk-${idx}`}
                      type="monotone" 
                      dataKey={`disk_${idx}`}
                      stroke={getIndexColor(idx, idxIndex)} 
                      name={`Disk GB (${idx})`}
                      connectNulls={true}
                      dot={false}
                      strokeWidth={2}
                    />
                  );
                })
              ) : (
                // Show single line when specific index is selected
                <Line type="monotone" dataKey="disk" stroke="#ffc658" name="Disk GB" strokeWidth={2} connectNulls={true} dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
          )}

          <h3>Network RX (Receive)</h3>
          {perfData.length === 0 ? (
            <NoDataMessage message="No network RX data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={perfData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="dateTime"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={100}
                tickFormatter={(value, index) => {
                  // Only show every 5th tick to reduce clutter
                  if (index % 5 !== 0) {
                    return '';
                  }
                  
                  // Parse the dateTime value
                  const date = new Date(value);
                  
                  // Check if date is valid
                  if (!isNaN(date.getTime())) {
                    // For multi-day ranges, show date + time
                    // For single-day ranges, show time only
                    if (perfData.length > 0) {
                      const firstDate = new Date(perfData[0].dateTime);
                      const lastDate = new Date(perfData[perfData.length - 1].dateTime);
                      // Check if data spans different calendar days
                      const firstDay = firstDate.toLocaleDateString();
                      const lastDay = lastDate.toLocaleDateString();
                      const spansMultipleDays = firstDay !== lastDay;
                      
                      if (spansMultipleDays) {
                        // Multi-day: show date + time
                        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                      } else {
                        // Single day: show time only
                        return date.toLocaleTimeString();
                      }
                    }
                    // Fallback: show date + time
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                  } else {
                    // Fallback if date parsing fails
                    return `Point ${index + 1}`;
                  }
                }}
              />
              <YAxis />
              <Tooltip />
              <Legend 
                content={(props) => {
                  if (index === 'all') {
                    if (!perfData || perfData.length === 0) {
                      return <CustomLegend payload={[{ value: 'RX MB', dataKey: 'network_rx', color: '#8884d8' }]} onToggle={toggleLineVisibility} />;
                    }
                    const indices = getUniqueIndices(perfData);
                    const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                    const payload = createLegendPayload(indices, 'RX MB', colors);
                    return <CustomLegend payload={payload} onToggle={toggleLineVisibility} />;
                  }
                  return <CustomLegend payload={[{ value: 'RX MB', dataKey: 'network_rx', color: '#8884d8' }]} onToggle={toggleLineVisibility} />;
                }}
              />
              {index === 'all' && perfData && perfData.length > 0 ? (
                // Show separate lines for each index when "All" is selected
                getUniqueIndices(perfData).map((idx, idxIndex) => {
                  const lineKey = `network_rx_${idx}`;
                  const isVisible = visibleLines[lineKey] === true || (visibleLines[lineKey] === undefined && Object.keys(visibleLines).length === 0) || visibleLines['all'] === true;
                  
                  // Only render the line if it's visible
                  if (!isVisible) return null;
                  
                  return (
                    <Line 
                      key={`rx-${idx}`}
                      type="monotone" 
                      dataKey={`network_rx_${idx}`}
                      stroke={getIndexColor(idx, idxIndex)} 
                      name={`RX MB (${idx})`}
                      connectNulls={true}
                      dot={false}
                      strokeWidth={2}
                    />
                  );
                })
              ) : (
                // Show single line when specific index is selected
                <Line type="monotone" dataKey="network_rx" stroke="#8884d8" name="RX MB" strokeWidth={2} connectNulls={true} dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
          )}

          <h3>Network TX (Transmit)</h3>
          {perfData.length === 0 ? (
            <NoDataMessage message="No network TX data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={perfData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="dateTime"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={100}
                tickFormatter={(value, index) => {
                  // Only show every 5th tick to reduce clutter
                  if (index % 5 !== 0) {
                    return '';
                  }
                  
                  // Parse the dateTime value
                  const date = new Date(value);
                  
                  // Check if date is valid
                  if (!isNaN(date.getTime())) {
                    // For multi-day ranges, show date + time
                    // For single-day ranges, show time only
                    if (perfData.length > 0) {
                      const firstDate = new Date(perfData[0].dateTime);
                      const lastDate = new Date(perfData[perfData.length - 1].dateTime);
                      // Check if data spans different calendar days
                      const firstDay = firstDate.toLocaleDateString();
                      const lastDay = lastDate.toLocaleDateString();
                      const spansMultipleDays = firstDay !== lastDay;
                      
                      if (spansMultipleDays) {
                        // Multi-day: show date + time
                        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                      } else {
                        // Single day: show time only
                        return date.toLocaleTimeString();
                      }
                    }
                    // Fallback: show date + time
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                  } else {
                    // Fallback if date parsing fails
                    return `Point ${index + 1}`;
                  }
                }}
              />
              <YAxis />
              <Tooltip />
              <Legend 
                content={(props) => {
                  if (index === 'all') {
                    if (!perfData || perfData.length === 0) {
                      return <CustomLegend payload={[{ value: 'TX MB', dataKey: 'network_tx', color: '#82ca9d' }]} onToggle={toggleLineVisibility} />;
                    }
                    const indices = getUniqueIndices(perfData);
                    const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                    const payload = createLegendPayload(indices, 'TX MB', colors);
                    return <CustomLegend payload={payload} onToggle={toggleLineVisibility} />;
                  }
                  return <CustomLegend payload={[{ value: 'TX MB', dataKey: 'network_tx', color: '#82ca9d' }]} onToggle={toggleLineVisibility} />;
                }}
              />
              {index === 'all' && perfData && perfData.length > 0 ? (
                // Show separate lines for each index when "All" is selected
                getUniqueIndices(perfData).map((idx, idxIndex) => {
                  const lineKey = `network_tx_${idx}`;
                  const isVisible = visibleLines[lineKey] === true || (visibleLines[lineKey] === undefined && Object.keys(visibleLines).length === 0) || visibleLines['all'] === true;
                  
                  // Only render the line if it's visible
                  if (!isVisible) return null;
                  
                  return (
                    <Line 
                      key={`tx-${idx}`}
                      type="monotone" 
                      dataKey={`network_tx_${idx}`}
                      stroke={getIndexColor(idx, idxIndex)} 
                      name={`TX MB (${idx})`}
                      connectNulls={true}
                      dot={false}
                      strokeWidth={2}
                    />
                  );
                })
              ) : (
                // Show single line when specific index is selected
                <Line type="monotone" dataKey="network_tx" stroke="#82ca9d" name="TX MB" strokeWidth={2} connectNulls={true} dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
          )}

        </div>
      );

      case 'engagement': return (
        <div>
          <h3>Session Duration</h3>
          {engagementData.length === 0 ? (
            <NoDataMessage message="No engagement session data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={engagementData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="dateTime"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={100}
                tickFormatter={(value, index) => {
                  // Only show every 5th tick to reduce clutter
                  if (index % 5 !== 0) {
                    return '';
                  }
                  
                  // Parse the dateTime value
                  const date = new Date(value);
                  
                  // Check if date is valid
                  if (!isNaN(date.getTime())) {
                    // For multi-day ranges, show date + time
                    // For single-day ranges, show time only
                    if (engagementData.length > 0) {
                      const firstDate = new Date(engagementData[0].dateTime);
                      const lastDate = new Date(engagementData[engagementData.length - 1].dateTime);
                      
                      // Check if data spans different calendar days
                      const firstDay = firstDate.toLocaleDateString();
                      const lastDay = lastDate.toLocaleDateString();
                      const spansMultipleDays = firstDay !== lastDay;
                      
                      if (spansMultipleDays) {
                        // Multi-day: show date + time
                        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                      } else {
                        // Single day: show time only
                        return date.toLocaleTimeString();
                      }
                    }
                    // Fallback: show date + time
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                  } else {
                    // Fallback if date parsing fails
                    return `Point ${index + 1}`;
                  }
                }}
              />
              <YAxis />
              <Tooltip />
              <Legend 
                content={(props) => {
                  if (!engagementData || engagementData.length === 0) {
                    return <CustomLegend payload={[{ value: 'Duration (min)', dataKey: 'duration', color: '#8884d8' }]} onToggle={toggleEngagementLineVisibility} visibilityState={engagementVisibleLines} />;
                  }
                  const indices = getUniqueIndices(engagementData);
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = createEngagementLegendPayload(indices, 'Duration', colors);
                  return <CustomLegend payload={payload} onToggle={toggleEngagementLineVisibility} visibilityState={engagementVisibleLines} />;
                }}
              />
              {getUniqueIndices(engagementData).map((index, idxIndex) => {
                const lineKey = `duration_${index}`;
                const isVisible = engagementVisibleLines['all'] === true || engagementVisibleLines[lineKey] === true;
                return isVisible ? (
                  <Line
                    key={lineKey}
                    type="monotone"
                    dataKey={lineKey}
                    stroke={getIndexColor(index, idxIndex)}
                    name={`Duration ${index}`}
                    strokeWidth={2}
                    connectNulls={true}
                    dot={false}
                  />
                ) : null;
              })}
            </LineChart>
          </ResponsiveContainer>
          )}

          <h3>Session Activity Count</h3>
          {engagementData.length === 0 ? (
            <NoDataMessage message="No engagement session data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={engagementData}>
          <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="dateTime"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={100}
                tickFormatter={(value, index) => {
                  // Only show every 5th tick to reduce clutter
                  if (index % 5 !== 0) {
                    return '';
                  }
                  
                  // Parse the dateTime value
                  const date = new Date(value);
                  
                  // Check if date is valid
                  if (!isNaN(date.getTime())) {
                    // For multi-day ranges, show date + time
                    // For single-day ranges, show time only
                    if (engagementData.length > 0) {
                      const firstDate = new Date(engagementData[0].dateTime);
                      const lastDate = new Date(engagementData[engagementData.length - 1].dateTime);
                      
                      // Check if data spans different calendar days
                      const firstDay = firstDate.toLocaleDateString();
                      const lastDay = lastDate.toLocaleDateString();
                      const spansMultipleDays = firstDay !== lastDay;
                      
                      if (spansMultipleDays) {
                        // Multi-day: show date + time
                        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                      } else {
                        // Single day: show time only
                        return date.toLocaleTimeString();
                      }
                    }
                    // Fallback: show date + time
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                  } else {
                    // Fallback if date parsing fails
                    return `Point ${index + 1}`;
                  }
                }}
              />
          <YAxis />
          <Tooltip />
              <Legend 
                content={(props) => {
                  if (!engagementData || engagementData.length === 0) {
                    return <CustomLegend payload={[{ value: 'Activity Count', dataKey: 'activity', color: '#82ca9d' }]} onToggle={toggleEngagementLineVisibility} visibilityState={engagementVisibleLines} />;
                  }
                  const indices = getUniqueIndices(engagementData);
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = createEngagementLegendPayload(indices, 'Activity', colors);
                  return <CustomLegend payload={payload} onToggle={toggleEngagementLineVisibility} visibilityState={engagementVisibleLines} />;
                }}
              />
              {getUniqueIndices(engagementData).map((index, idxIndex) => {
                const lineKey = `activity_${index}`;
                const isVisible = engagementVisibleLines['all'] === true || engagementVisibleLines[lineKey] === true;
                return isVisible ? (
                  <Line
                    key={lineKey}
                    type="monotone"
                    dataKey={lineKey}
                    stroke={getIndexColor(index, idxIndex)}
                    name={`Activity ${index}`}
                    strokeWidth={2}
                    connectNulls={true}
                    dot={false}
                  />
                ) : null;
              })}
            </LineChart>
      </ResponsiveContainer>
          )}

          <h3>Command Engagement Analysis</h3>
          {(() => {
            // Build category-by-index dataset strictly from data.command_monitoring.command_patterns
            const dataset = commandPatternData;
            if (!dataset || dataset.length === 0) {
              return <NoDataMessage message="No command engagement data available." />;
            }
            const indices = getIndicesFromPatternData(dataset);
            return (
              <ResponsiveContainer width="100%" height={330}>
                <ComposedChart data={dataset}>
          <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
          <Tooltip />
                  <Legend content={() => {
                    const colors = indices.map((_, i) => getIndexColor(indices[i], i));
                    const payload = createCommandEngagementLegendPayload(indices, 'Commands', colors);
                    return <CustomLegend payload={payload} onToggle={toggleCommandEngagementLineVisibility} visibilityState={commandEngagementVisibleLines} />;
                  }} />
                  {indices.map((idx, i) => (
                    <Bar key={idx} dataKey={`count_${idx}`} name={idx} fill={getIndexColor(idx, i)} />
                  ))}
        </ComposedChart>
      </ResponsiveContainer>
            );
          })()}

          <h3>Real-time Engagement Metrics</h3>
          {engagementMetrics.data.length === 0 ? (
            <NoDataMessage message="No real-time engagement metrics available." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={(() => {
              // Process data to support multi-index structure
              const processedData: any[] = [];
              const indices = getUniqueIndices(engagementMetrics.data);
              
              // Group data by timestamp and index
              const groupedData: Record<string, Record<string, any>> = {};
              
              engagementMetrics.data.forEach((d: any) => {
                const timestamp = new Date(d.timestamp).toLocaleString();
                const sourceIndex = d.sourceIndex || 'unknown';
                
                if (!groupedData[timestamp]) {
                  groupedData[timestamp] = { timestamp };
                }
                
                // Add metrics for this index using actual available fields
                groupedData[timestamp][`duration_${sourceIndex}`] = d.data?.duration_minutes || d.data?.duration || d.data?.session_duration || d.data?.time_spent || d.data?.minutes || 0;
                groupedData[timestamp][`activity_${sourceIndex}`] = d.data?.activity_count || d.data?.activities || d.data?.commands_executed || d.data?.interactions || d.data?.count || 0;
                groupedData[timestamp][`engagement_${sourceIndex}`] = (d.data?.activity_count || 0) * (d.data?.duration_minutes || 1); // Calculate engagement as activity per minute
              });
              
              return Object.values(groupedData);
            })()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timestamp" 
                angle={-45} 
                textAnchor="end" 
                height={100}
                tick={{ fontSize: 10 }}
                tickFormatter={(value, index) => {
                  // Only show every 5th tick to reduce clutter
                  if (index % 5 !== 0) {
                    return '';
                  }
                  return value;
                }}
              />
              <YAxis />
              <Tooltip />
              <Legend 
                content={(props) => {
                  const indices = getUniqueIndices(engagementMetrics.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Session Duration', dataKey: 'duration', color: '#8884d8' },
                      { value: 'Activity Count', dataKey: 'activity', color: '#82ca9d' },
                      { value: 'Engagement Score', dataKey: 'engagement', color: '#ffc658' }
                    ]} onToggle={toggleEngagementMetricsLineVisibility} visibilityState={engagementMetricsVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Engagement', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Duration (${idx})`, 
                      dataKey: `duration_${idx}`, 
                      color: colors[i] 
                    })),
                    ...indices.map((idx, i) => ({ 
                      value: `Activity (${idx})`, 
                      dataKey: `activity_${idx}`, 
                      color: colors[i] 
                    })),
                    ...indices.map((idx, i) => ({ 
                      value: `Engagement (${idx})`, 
                      dataKey: `engagement_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleEngagementMetricsLineVisibility} visibilityState={engagementMetricsVisibleLines} />;
                }}
              />
              {getUniqueIndices(engagementMetrics.data).map((idx, idxIndex) => {
                const durationKey = `duration_${idx}`;
                const activityKey = `activity_${idx}`;
                const engagementKey = `engagement_${idx}`;
                
                const isDurationVisible = engagementMetricsVisibleLines[durationKey] === true || 
                                         (engagementMetricsVisibleLines[durationKey] === undefined && Object.keys(engagementMetricsVisibleLines).length === 0) || 
                                         engagementMetricsVisibleLines['all'] === true;
                
                const isActivityVisible = engagementMetricsVisibleLines[activityKey] === true || 
                                         (engagementMetricsVisibleLines[activityKey] === undefined && Object.keys(engagementMetricsVisibleLines).length === 0) || 
                                         engagementMetricsVisibleLines['all'] === true;
                
                const isEngagementVisible = engagementMetricsVisibleLines[engagementKey] === true || 
                                           (engagementMetricsVisibleLines[engagementKey] === undefined && Object.keys(engagementMetricsVisibleLines).length === 0) || 
                                           engagementMetricsVisibleLines['all'] === true;
                
                return (
                  <React.Fragment key={`engagement-metrics-${idx}`}>
                    {isDurationVisible && (
                      <Line
                        type="monotone"
                        dataKey={durationKey}
                        stroke={getIndexColor(idx, idxIndex)}
                        name={`Duration ${idx}`}
                        strokeWidth={2}
                        connectNulls={true}
                        dot={false}
                      />
                    )}
                    {isActivityVisible && (
                      <Line
                        type="monotone"
                        dataKey={activityKey}
                        stroke={getIndexColor(idx, idxIndex)}
                        name={`Activity ${idx}`}
                        strokeWidth={2}
                        connectNulls={true}
                        dot={false}
                        strokeDasharray="5 5"
                      />
                    )}
                    {isEngagementVisible && (
                      <Line
                        type="monotone"
                        dataKey={engagementKey}
                        stroke={getIndexColor(idx, idxIndex)}
                        name={`Engagement ${idx}`}
                        strokeWidth={2}
                        connectNulls={true}
                        dot={false}
                        strokeDasharray="10 5"
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </LineChart>
          </ResponsiveContainer>
          )}

          <h3>Session Duration Distribution</h3>
          <ResponsiveContainer width="100%" height={330}>
            <PieChart>
              <Pie
                data={(() => {
                  const indices = getUniqueIndices(engagementSessions.data);
                  if (indices.length === 0) {
                    return [
                      { name: 'Short (< 30min)', value: engagementData.filter(d => d.duration < 30).length },
                      { name: 'Medium (30-60min)', value: engagementData.filter(d => d.duration >= 30 && d.duration < 60).length },
                      { name: 'Long (> 60min)', value: engagementData.filter(d => d.duration >= 60).length }
                    ];
                  }
                  
                  // Group by duration level and index
                  const durationGroups: Record<string, Record<string, number>> = {};
                  engagementSessions.data.forEach(d => {
                    let durationLevel = 'Short (< 30min)';
                    const duration = d.data?.duration_minutes || 0;
                    if (duration >= 60) durationLevel = 'Long (> 60min)';
                    else if (duration >= 30) durationLevel = 'Medium (30-60min)';
                    
                    const sourceIndex = (d as any).sourceIndex || 'unknown';
                    
                    if (!durationGroups[durationLevel]) {
                      durationGroups[durationLevel] = {};
                    }
                    durationGroups[durationLevel][sourceIndex] = (durationGroups[durationLevel][sourceIndex] || 0) + 1;
                  });
                  
                  const result: any[] = [];
                  Object.keys(durationGroups).forEach(durationLevel => {
                    indices.forEach(idx => {
                      const count = durationGroups[durationLevel][idx] || 0;
                      if (count > 0) {
                        result.push({
                          name: `${durationLevel} (${idx})`,
                          value: count,
                          durationLevel: durationLevel,
                          index: idx
                        });
                      }
                    });
                  });
                  
                  return result;
                })()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {(() => {
                  const indices = getUniqueIndices(engagementSessions.data);
                  return indices.map((idx, idxIndex) => (
                    <Cell key={`cell-${idx}`} fill={getIndexColor(idx, idxIndex)} />
                  ));
                })()}
              </Pie>
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(engagementSessions.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Short Sessions', dataKey: 'short', color: '#8884d8' },
                      { value: 'Medium Sessions', dataKey: 'medium', color: '#82ca9d' },
                      { value: 'Long Sessions', dataKey: 'long', color: '#ffc658' }
                    ]} onToggle={() => {}} visibilityState={{}} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Session Durations', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Session Durations (${idx})`, 
                      dataKey: `duration_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={() => {}} visibilityState={{}} />;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );

      case 'learning': return (
        <div>
          <h3>Skills Progress Overview</h3>
          {skillData.length === 0 ? (
            <NoDataMessage message="No learning progress data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(learningProgress.data);
              const processedData: any[] = [];
              
              // Group skills by skill name and index
              const skillGroups: Record<string, Record<string, any>> = {};
              
              learningProgress.data.forEach(d => {
                const skill = d.data.skill || 'Unknown';
                const sourceIndex = (d as any).sourceIndex || 'unknown';
                
                if (!skillGroups[skill]) {
                  skillGroups[skill] = { skill };
                }
                
                // Add progress for this index
                skillGroups[skill][`progress_${sourceIndex}`] = d.data.progress_percent || 0;
              });
              
              return Object.values(skillGroups);
            })()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="skill" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(learningProgress.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[{ value: 'Progress %', dataKey: 'progress', color: '#8884d8' }]} onToggle={toggleLearningProgressBarVisibility} visibilityState={learningProgressVisibleBars} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Progress', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Progress (${idx})`, 
                      dataKey: `progress_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleLearningProgressBarVisibility} visibilityState={learningProgressVisibleBars} />;
                }}
              />
              {getUniqueIndices(learningProgress.data).map((idx, idxIndex) => {
                const barKey = `progress_${idx}`;
                const isVisible = learningProgressVisibleBars[barKey] === true || 
                                 (learningProgressVisibleBars[barKey] === undefined && Object.keys(learningProgressVisibleBars).length === 0) || 
                                 learningProgressVisibleBars['all'] === true;
                
                return isVisible ? (
                  <Bar key={idx} dataKey={barKey} name={idx} fill={getIndexColor(idx, idxIndex)} />
                ) : null;
              })}
            </BarChart>
          </ResponsiveContainer>
          )}

          <h3>AI-Powered Skill Analytics</h3>
          {skillAnalyticsData.length === 0 ? (
            <NoDataMessage message="No skill analytics data available." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <ComposedChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(skillProgressAnalytics.data);
              
              // Group skills by skill name and index
              const skillGroups: Record<string, Record<string, any>> = {};
              
              skillProgressAnalytics.data.forEach(d => {
                const skill = d.data?.skill || 'Unknown';
                const sourceIndex = (d as any).sourceIndex || 'unknown';
                
                if (!skillGroups[skill]) {
                  skillGroups[skill] = { skill };
                }
                
                // Add proficiency and confidence for this index
                skillGroups[skill][`proficiency_${sourceIndex}`] = (d.data as any)?.proficiency_score || 0;
                skillGroups[skill][`confidence_${sourceIndex}`] = (d.data as any)?.confidence_level || 0;
              });
              
              return Object.values(skillGroups);
            })()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="skill" angle={-45} textAnchor="end" height={80} />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(skillProgressAnalytics.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Proficiency Score', dataKey: 'proficiency', color: '#8884d8' },
                      { value: 'Confidence Level', dataKey: 'confidence', color: '#82ca9d' }
                    ]} onToggle={toggleSkillAnalyticsLineVisibility} visibilityState={skillAnalyticsVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Proficiency', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Proficiency (${idx})`, 
                      dataKey: `proficiency_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleSkillAnalyticsLineVisibility} visibilityState={skillAnalyticsVisibleLines} />;
                }}
              />
              {getUniqueIndices(skillProgressAnalytics.data).map((idx, idxIndex) => {
                const barKey = `proficiency_${idx}`;
                const lineKey = `confidence_${idx}`;
                const isVisible = skillAnalyticsVisibleLines[barKey] === true || 
                                 (skillAnalyticsVisibleLines[barKey] === undefined && Object.keys(skillAnalyticsVisibleLines).length === 0) || 
                                 skillAnalyticsVisibleLines['all'] === true;
                
                return isVisible ? (
                  <>
                    <Bar key={`proficiency-${idx}`} yAxisId="left" dataKey={barKey} name={`Proficiency ${idx}`} fill={getIndexColor(idx, idxIndex)} />
                    <Line key={`confidence-${idx}`} yAxisId="right" type="monotone" dataKey={lineKey} stroke={getIndexColor(idx, idxIndex)} name={`Confidence ${idx}`} strokeWidth={2} connectNulls={true} dot={false} />
                  </>
                ) : null;
              })}
            </ComposedChart>
          </ResponsiveContainer>
          )}

          <h3>Cross-Server Skill Comparison</h3>
          {skillComparisonData.length === 0 ? (
            <NoDataMessage message="No cross-server skill comparison data available." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(skillCrossComparison.data);
              
              // Group skills by skill name and index
              const skillGroups: Record<string, Record<string, any>> = {};
              
              skillCrossComparison.data.forEach(d => {
                const skill = d.data?.skill || 'Unknown';
                const sourceIndex = (d as any).sourceIndex || 'unknown';
                
                if (!skillGroups[skill]) {
                  skillGroups[skill] = { skill };
                }
                
                // Add progress and rank for this index
                skillGroups[skill][`progress_${sourceIndex}`] = d.data?.progress_percent || 0;
                skillGroups[skill][`rank_${sourceIndex}`] = (d.data as any)?.rank || 0;
              });
              
              return Object.values(skillGroups).slice(0, 20);
            })()}>
          <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="skill" angle={-45} textAnchor="end" height={80} />
          <YAxis />
          <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(skillCrossComparison.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Progress', dataKey: 'progress', color: '#8884d8' },
                      { value: 'Rank', dataKey: 'rank', color: '#ffc658' }
                    ]} onToggle={toggleSkillComparisonBarVisibility} visibilityState={skillComparisonVisibleBars} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Progress', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Progress (${idx})`, 
                      dataKey: `progress_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleSkillComparisonBarVisibility} visibilityState={skillComparisonVisibleBars} />;
                }}
              />
              {getUniqueIndices(skillCrossComparison.data).map((idx, idxIndex) => {
                const progressKey = `progress_${idx}`;
                const rankKey = `rank_${idx}`;
                const isVisible = skillComparisonVisibleBars[progressKey] === true || 
                                 (skillComparisonVisibleBars[progressKey] === undefined && Object.keys(skillComparisonVisibleBars).length === 0) || 
                                 skillComparisonVisibleBars['all'] === true;
                
                return isVisible ? (
                  <>
                    <Bar key={`progress-${idx}`} dataKey={progressKey} name={`Progress ${idx}`} fill={getIndexColor(idx, idxIndex)} />
                    <Bar key={`rank-${idx}`} dataKey={rankKey} name={`Rank ${idx}`} fill={getIndexColor(idx, idxIndex)} opacity={0.7} />
                  </>
                ) : null;
              })}
        </BarChart>
      </ResponsiveContainer>
          )}

          <h3>Learning Level Distribution</h3>
          <ResponsiveContainer width="100%" height={330}>
            <PieChart>
              <Pie
                data={(() => {
                  const indices = getUniqueIndices(learningProgress.data);
                  if (indices.length === 0) {
                    return [
                      { name: 'Beginner', value: skillData.filter(s => s.level === 'Beginner').length },
                      { name: 'Intermediate', value: skillData.filter(s => s.level === 'Intermediate').length },
                      { name: 'Advanced', value: skillData.filter(s => s.level === 'Advanced').length }
                    ];
                  }
                  
                  // Group by level and index
                  const levelGroups: Record<string, Record<string, number>> = {};
                  learningProgress.data.forEach(d => {
                    const level = d.data?.level || 'Beginner';
                    const sourceIndex = (d as any).sourceIndex || 'unknown';
                    
                    if (!levelGroups[level]) {
                      levelGroups[level] = {};
                    }
                    levelGroups[level][sourceIndex] = (levelGroups[level][sourceIndex] || 0) + 1;
                  });
                  
                  const result: any[] = [];
                  Object.keys(levelGroups).forEach(level => {
                    indices.forEach(idx => {
                      const count = levelGroups[level][idx] || 0;
                      if (count > 0) {
                        result.push({
                          name: `${level} (${idx})`,
                          value: count,
                          level: level,
                          index: idx
                        });
                      }
                    });
                  });
                  
                  return result;
                })()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {(() => {
                  const indices = getUniqueIndices(learningProgress.data);
                  return indices.map((idx, idxIndex) => (
                    <Cell key={`cell-${idx}`} fill={getIndexColor(idx, idxIndex)} />
                  ));
                })()}
              </Pie>
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(learningProgress.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Beginner', dataKey: 'beginner', color: '#8884d8' },
                      { value: 'Intermediate', dataKey: 'intermediate', color: '#82ca9d' },
                      { value: 'Advanced', dataKey: 'advanced', color: '#ffc658' }
                    ]} onToggle={() => {}} visibilityState={{}} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Levels', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Levels (${idx})`, 
                      dataKey: `level_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={() => {}} visibilityState={{}} />;
                }}
              />
            </PieChart>
          </ResponsiveContainer>

        </div>
      );

      case 'usage': return (
        <div>
          <h3>Application Usage Analysis</h3>
          {appUsageData.length === 0 ? (
            <NoDataMessage message="No app usage data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(appUsageStats.data);
              
              // Group apps by app name and index
              const appGroups: Record<string, Record<string, any>> = {};
              
              appUsageStats.data.forEach(d => {
                const app = d.data.app_name || 'Unknown';
                const sourceIndex = (d as any).sourceIndex || 'unknown';
                
                if (!appGroups[app]) {
                  appGroups[app] = { app };
                }
                
                // Add usage for this index
                appGroups[app][`usage_${sourceIndex}`] = d.data.usage_minutes || 0;
              });
              
              return Object.values(appGroups).slice(0, 15);
            })()}>
          <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="app" angle={-45} textAnchor="end" height={80} />
          <YAxis />
          <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(appUsageStats.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[{ value: 'Usage (minutes)', dataKey: 'usage', color: '#8884d8' }]} onToggle={toggleAppUsageBarVisibility} visibilityState={appUsageVisibleBars} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Usage', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Usage (${idx})`, 
                      dataKey: `usage_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleAppUsageBarVisibility} visibilityState={appUsageVisibleBars} />;
                }}
              />
              {getUniqueIndices(appUsageStats.data).map((idx, idxIndex) => {
                const barKey = `usage_${idx}`;
                const isVisible = appUsageVisibleBars[barKey] === true || 
                                 (appUsageVisibleBars[barKey] === undefined && Object.keys(appUsageVisibleBars).length === 0) || 
                                 appUsageVisibleBars['all'] === true;
                
                return isVisible ? (
                  <Bar key={idx} dataKey={barKey} name={idx} fill={getIndexColor(idx, idxIndex)} />
                ) : null;
              })}
            </BarChart>
      </ResponsiveContainer>
          )}

          <h3>Daily Activity Patterns</h3>
          {dailyActivityData.length === 0 ? (
            <NoDataMessage message="No daily activity data available." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <ComposedChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(dailyActivity.data);
              
              // Group by date and index
              const dateGroups: Record<string, Record<string, any>> = {};
              
              dailyActivity.data.forEach(d => {
                const date = d.data?.date || 'Unknown';
                const sourceIndex = (d as any).sourceIndex || 'unknown';
                
                if (!dateGroups[date]) {
                  dateGroups[date] = { date };
                }
                
                // Add hours and productivity for this index
                dateGroups[date][`hours_${sourceIndex}`] = d.data?.total_hours || 0;
                dateGroups[date][`productivity_${sourceIndex}`] = d.data?.productivity_score || 0;
              });
              
              return Object.values(dateGroups);
            })()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" angle={-45} textAnchor="end" height={80} />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(dailyActivity.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Total Hours', dataKey: 'hours', color: '#8884d8' },
                      { value: 'Productivity Score', dataKey: 'productivity', color: '#82ca9d' }
                    ]} onToggle={toggleDailyActivityLineVisibility} visibilityState={dailyActivityVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Hours', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Hours (${idx})`, 
                      dataKey: `hours_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleDailyActivityLineVisibility} visibilityState={dailyActivityVisibleLines} />;
                }}
              />
              {getUniqueIndices(dailyActivity.data).map((idx, idxIndex) => {
                const hoursKey = `hours_${idx}`;
                const productivityKey = `productivity_${idx}`;
                const isVisible = dailyActivityVisibleLines[hoursKey] === true || 
                                 (dailyActivityVisibleLines[hoursKey] === undefined && Object.keys(dailyActivityVisibleLines).length === 0) || 
                                 dailyActivityVisibleLines['all'] === true;
                
                return isVisible ? (
                  <>
                    <Bar key={`hours-${idx}`} yAxisId="left" dataKey={hoursKey} name={`Hours ${idx}`} fill={getIndexColor(idx, idxIndex)} />
                    <Line key={`productivity-${idx}`} yAxisId="right" type="monotone" dataKey={productivityKey} stroke={getIndexColor(idx, idxIndex)} name={`Productivity ${idx}`} strokeWidth={2} connectNulls={true} dot={false} />
                  </>
                ) : null;
              })}
            </ComposedChart>
          </ResponsiveContainer>
          )}

          <h3>Window Usage Patterns</h3>
          {windows.data.length === 0 ? (
            <NoDataMessage message="No window usage data available." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(windows.data);
              
              // Group by process and index
              const processGroups: Record<string, Record<string, any>> = {};
              
              windows.data.slice(0, 10).forEach(win => {
                const process = win.data?.process_name || 'Unknown';
                const sourceIndex = (win as any).sourceIndex || 'unknown';
                
                if (!processGroups[process]) {
                  processGroups[process] = { 
                    process,
                    title: (win.data?.window_title || 'Unknown').substring(0, 20) + '...'
                  };
                }
                
                // Add duration for this index
                processGroups[process][`duration_${sourceIndex}`] = (win.data?.duration_seconds || 0) / 60; // Convert to minutes
              });
              
              return Object.values(processGroups);
            })()}>
          <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="process" angle={-45} textAnchor="end" height={80} />
          <YAxis />
          <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(windows.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Duration (min)', dataKey: 'duration', color: '#8884d8' }
                    ]} onToggle={toggleWindowUsageLineVisibility} visibilityState={windowUsageVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Duration', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Duration (${idx})`, 
                      dataKey: `duration_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleWindowUsageLineVisibility} visibilityState={windowUsageVisibleLines} />;
                }}
              />
              {getUniqueIndices(windows.data).map((idx, idxIndex) => {
                const durationKey = `duration_${idx}`;
                const isVisible = windowUsageVisibleLines[durationKey] === true || 
                                 (windowUsageVisibleLines[durationKey] === undefined && Object.keys(windowUsageVisibleLines).length === 0) || 
                                 windowUsageVisibleLines['all'] === true;
                
                return isVisible ? (
                  <Bar key={`duration-${idx}`} dataKey={durationKey} name={`Duration ${idx}`} fill={getIndexColor(idx, idxIndex)} />
                ) : null;
              })}
            </BarChart>
      </ResponsiveContainer>
          )}

          <h3>App Category Distribution</h3>
          <ResponsiveContainer width="100%" height={330}>
            <PieChart>
              <Pie
                data={(() => {
                  const indices = getUniqueIndices(appUsageStats.data);
                  if (indices.length === 0) {
                    return Object.entries(
                      appUsageData.reduce((acc, app) => {
                        acc[app.category] = (acc[app.category] || 0) + app.usage;
                        return acc;
                      }, {} as Record<string, number>)
                    ).map(([category, usage]) => ({ name: category, value: usage }));
                  }
                  
                  // Group by category and index
                  const categoryGroups: Record<string, Record<string, number>> = {};
                  appUsageStats.data.forEach(d => {
                    const category = d.data?.category || 'Unknown';
                    const sourceIndex = (d as any).sourceIndex || 'unknown';
                    const usage = d.data?.usage_minutes || 0;
                    
                    if (!categoryGroups[category]) {
                      categoryGroups[category] = {};
                    }
                    categoryGroups[category][sourceIndex] = (categoryGroups[category][sourceIndex] || 0) + usage;
                  });
                  
                  const result: any[] = [];
                  Object.keys(categoryGroups).forEach(category => {
                    indices.forEach(idx => {
                      const usage = categoryGroups[category][idx] || 0;
                      if (usage > 0) {
                        result.push({
                          name: `${category} (${idx})`,
                          value: usage,
                          category: category,
                          index: idx
                        });
                      }
                    });
                  });
                  
                  return result;
                })()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {(() => {
                  const indices = getUniqueIndices(appUsageStats.data);
                  return indices.map((idx, idxIndex) => (
                    <Cell key={`cell-${idx}`} fill={getIndexColor(idx, idxIndex)} />
                  ));
                })()}
              </Pie>
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(appUsageStats.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Development', dataKey: 'development', color: '#8884d8' },
                      { value: 'Productivity', dataKey: 'productivity', color: '#82ca9d' },
                      { value: 'Entertainment', dataKey: 'entertainment', color: '#ffc658' }
                    ]} onToggle={() => {}} visibilityState={{}} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Categories', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Categories (${idx})`, 
                      dataKey: `category_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={() => {}} visibilityState={{}} />;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );

      case 'risk': return (
        <div>
          <h3>Dropout Risk Assessment</h3>
          {dropoutRiskData.length === 0 ? (
            <NoDataMessage message="No dropout risk assessment data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(dropoutRiskAssessment.data);
              
              // Group by user and index
              const userGroups: Record<string, Record<string, any>> = {};
              
              dropoutRiskAssessment.data.slice(0, 20).forEach(d => {
                const user = d.data?.user_id || 'Unknown';
                const sourceIndex = (d as any).sourceIndex || 'unknown';
                
                if (!userGroups[user]) {
                  userGroups[user] = { user };
                }
                
                // Add risk score for this index
                userGroups[user][`riskScore_${sourceIndex}`] = d.data?.risk_score || 0;
              });
              
              return Object.values(userGroups);
            })()}>
          <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="user" angle={-45} textAnchor="end" height={80} />
          <YAxis />
          <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(dropoutRiskAssessment.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Risk Score', dataKey: 'riskScore', color: '#ff6b6b' }
                    ]} onToggle={toggleDropoutRiskLineVisibility} visibilityState={dropoutRiskVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Risk Scores', dataKey: 'all', color: '#ff6b6b' },
                    ...indices.map((idx, i) => ({ 
                      value: `Risk Score (${idx})`, 
                      dataKey: `riskScore_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleDropoutRiskLineVisibility} visibilityState={dropoutRiskVisibleLines} />;
                }}
              />
              {getUniqueIndices(dropoutRiskAssessment.data).map((idx, idxIndex) => {
                const riskKey = `riskScore_${idx}`;
                const isVisible = dropoutRiskVisibleLines[riskKey] === true || 
                                 (dropoutRiskVisibleLines[riskKey] === undefined && Object.keys(dropoutRiskVisibleLines).length === 0) || 
                                 dropoutRiskVisibleLines['all'] === true;
                
                return isVisible ? (
                  <Bar key={`risk-${idx}`} dataKey={riskKey} name={`Risk Score ${idx}`} fill={getIndexColor(idx, idxIndex)} />
                ) : null;
              })}
        </BarChart>
      </ResponsiveContainer>
          )}

          <h3>Risk Factor Analysis</h3>
          {dropoutRiskData.length === 0 ? (
            <NoDataMessage message="No risk factor data available." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <PieChart>
              <Pie
                data={(() => {
                  const indices = getUniqueIndices(dropoutRiskAssessment.data);
                  if (indices.length === 0) {
                    return Object.entries(
                      dropoutRiskData.reduce((acc: any, user) => {
                        user.factors.forEach((factor: any) => {
                          acc[factor] = (acc[factor] || 0) + 1;
                        });
                        return acc;
                      }, {} as Record<string, number>)
                    ).map(([factor, count]) => ({ name: factor, value: count }));
                  }
                  
                  // Group by factor and index
                  const factorGroups: Record<string, Record<string, number>> = {};
                  dropoutRiskAssessment.data.forEach(d => {
                    const factors = d.data?.factors || [];
                    const sourceIndex = (d as any).sourceIndex || 'unknown';
                    
                    factors.forEach((factor: string) => {
                      if (!factorGroups[factor]) {
                        factorGroups[factor] = {};
                      }
                      factorGroups[factor][sourceIndex] = (factorGroups[factor][sourceIndex] || 0) + 1;
                    });
                  });
                  
                  const result: any[] = [];
                  Object.keys(factorGroups).forEach(factor => {
                    indices.forEach(idx => {
                      const count = factorGroups[factor][idx] || 0;
                      if (count > 0) {
                        result.push({
                          name: `${factor} (${idx})`,
                          value: count,
                          factor: factor,
                          index: idx
                        });
                      }
                    });
                  });
                  
                  return result;
                })()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#ff6b6b"
                dataKey="value"
              >
                {(() => {
                  const indices = getUniqueIndices(dropoutRiskAssessment.data);
                  return indices.map((idx, idxIndex) => (
                    <Cell key={`cell-${idx}`} fill={getIndexColor(idx, idxIndex)} />
                  ));
                })()}
              </Pie>
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(dropoutRiskAssessment.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Low Activity', dataKey: 'low_activity', color: '#ff6b6b' },
                      { value: 'Poor Performance', dataKey: 'poor_performance', color: '#ffc658' },
                      { value: 'Late Submissions', dataKey: 'late_submissions', color: '#82ca9d' }
                    ]} onToggle={() => {}} visibilityState={{}} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Risk Factors', dataKey: 'all', color: '#ff6b6b' },
                    ...indices.map((idx, i) => ({ 
                      value: `Risk Factors (${idx})`, 
                      dataKey: `factor_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={() => {}} visibilityState={{}} />;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          )}

          <h3>Risk Prediction Distribution</h3>
          {dropoutRiskData.length === 0 ? (
            <NoDataMessage message="No risk prediction data available." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <PieChart>
              <Pie
                data={(() => {
                  const indices = getUniqueIndices(dropoutRiskAssessment.data);
                  if (indices.length === 0) {
                    return [
                      { name: 'Low Risk', value: dropoutRiskData.filter(d => d.prediction === 'low').length },
                      { name: 'Medium Risk', value: dropoutRiskData.filter(d => d.prediction === 'medium').length },
                      { name: 'High Risk', value: dropoutRiskData.filter(d => d.prediction === 'high').length }
                    ];
                  }
                  
                  // Group by prediction level and index
                  const predictionGroups: Record<string, Record<string, number>> = {};
                  dropoutRiskAssessment.data.forEach(d => {
                    const prediction = 'low'; // Default prediction value
                    const sourceIndex = (d as any).sourceIndex || 'unknown';
                    
                    if (!predictionGroups[prediction]) {
                      predictionGroups[prediction] = {};
                    }
                    predictionGroups[prediction][sourceIndex] = (predictionGroups[prediction][sourceIndex] || 0) + 1;
                  });
                  
                  const result: any[] = [];
                  Object.keys(predictionGroups).forEach(prediction => {
                    indices.forEach(idx => {
                      const count = predictionGroups[prediction][idx] || 0;
                      if (count > 0) {
                        result.push({
                          name: `${prediction.charAt(0).toUpperCase() + prediction.slice(1)} Risk (${idx})`,
                          value: count,
                          prediction: prediction,
                          index: idx
                        });
                      }
                    });
                  });
                  
                  return result;
                })()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#ff6b6b"
                dataKey="value"
              >
                {(() => {
                  const indices = getUniqueIndices(dropoutRiskAssessment.data);
                  return indices.map((idx, idxIndex) => (
                    <Cell key={`cell-${idx}`} fill={getIndexColor(idx, idxIndex)} />
                  ));
                })()}
              </Pie>
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(dropoutRiskAssessment.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Low Risk', dataKey: 'low_risk', color: '#4caf50' },
                      { value: 'Medium Risk', dataKey: 'medium_risk', color: '#ffa726' },
                      { value: 'High Risk', dataKey: 'high_risk', color: '#ff6b6b' }
                    ]} onToggle={() => {}} visibilityState={{}} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Risk Predictions', dataKey: 'all', color: '#ff6b6b' },
                    ...indices.map((idx, i) => ({ 
                      value: `Risk Predictions (${idx})`, 
                      dataKey: `prediction_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={() => {}} visibilityState={{}} />;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          )}
        </div>
      );

      case 'analytics': return (
        <div>
          <h3>Daily Activity Analytics</h3>
          <ResponsiveContainer width="100%" height={330}>
            <ComposedChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(dailyActivity.data);
              
              // Group by date and index
              const dateGroups: Record<string, Record<string, any>> = {};
              
              dailyActivity.data.forEach(d => {
                const date = d.data?.date || 'Unknown';
                const sourceIndex = (d as any).sourceIndex || 'unknown';
                
                if (!dateGroups[date]) {
                  dateGroups[date] = { date };
                }
                
                // Add hours and productivity for this index
                dateGroups[date][`hours_${sourceIndex}`] = d.data?.total_hours || 0;
                dateGroups[date][`productivity_${sourceIndex}`] = d.data?.productivity_score || 0;
              });
              
              return Object.values(dateGroups);
            })()}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
          <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(dailyActivity.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Hours', dataKey: 'hours', color: '#8884d8' },
                      { value: 'Productivity Score', dataKey: 'productivity', color: '#ffc658' }
                    ]} onToggle={toggleDailyActivityLineVisibility} visibilityState={dailyActivityVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Hours', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Hours (${idx})`, 
                      dataKey: `hours_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleDailyActivityLineVisibility} visibilityState={dailyActivityVisibleLines} />;
                }}
              />
              {getUniqueIndices(dailyActivity.data).map((idx, idxIndex) => {
                const hoursKey = `hours_${idx}`;
                const productivityKey = `productivity_${idx}`;
                const isVisible = dailyActivityVisibleLines[hoursKey] === true || 
                                 (dailyActivityVisibleLines[hoursKey] === undefined && Object.keys(dailyActivityVisibleLines).length === 0) || 
                                 dailyActivityVisibleLines['all'] === true;
                
                return isVisible ? (
                  <>
                    <Bar key={`hours-${idx}`} yAxisId="left" dataKey={hoursKey} name={`Hours ${idx}`} fill={getIndexColor(idx, idxIndex)} />
                    <Line key={`productivity-${idx}`} yAxisId="right" type="monotone" dataKey={productivityKey} stroke={getIndexColor(idx, idxIndex)} name={`Productivity ${idx}`} strokeWidth={2} connectNulls={true} dot={false} />
                  </>
                ) : null;
              })}
        </ComposedChart>
      </ResponsiveContainer>

          <h3>Productivity Trends</h3>
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(dailyActivity.data);
              
              // Group by date and index
              const dateGroups: Record<string, Record<string, any>> = {};
              
              dailyActivity.data.forEach(d => {
                const date = d.data?.date || 'Unknown';
                const sourceIndex = (d as any).sourceIndex || 'unknown';
                
                if (!dateGroups[date]) {
                  dateGroups[date] = { date };
                }
                
                // Add productivity and hours for this index
                dateGroups[date][`productivity_${sourceIndex}`] = d.data?.productivity_score || 0;
                dateGroups[date][`hours_${sourceIndex}`] = d.data?.total_hours || 0;
              });
              
              return Object.values(dateGroups);
            })()}>
          <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(dailyActivity.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Productivity Score', dataKey: 'productivity', color: '#82ca9d' },
                      { value: 'Hours', dataKey: 'hours', color: '#8884d8' }
                    ]} onToggle={toggleDailyActivityLineVisibility} visibilityState={dailyActivityVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Productivity', dataKey: 'all', color: '#82ca9d' },
                    ...indices.map((idx, i) => ({ 
                      value: `Productivity (${idx})`, 
                      dataKey: `productivity_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleDailyActivityLineVisibility} visibilityState={dailyActivityVisibleLines} />;
                }}
              />
              {getUniqueIndices(dailyActivity.data).map((idx, idxIndex) => {
                const productivityKey = `productivity_${idx}`;
                const hoursKey = `hours_${idx}`;
                const isVisible = dailyActivityVisibleLines[productivityKey] === true || 
                                 (dailyActivityVisibleLines[productivityKey] === undefined && Object.keys(dailyActivityVisibleLines).length === 0) || 
                                 dailyActivityVisibleLines['all'] === true;
                
                return isVisible ? (
                  <>
                    <Line key={`productivity-${idx}`} type="monotone" dataKey={productivityKey} stroke={getIndexColor(idx, idxIndex)} name={`Productivity ${idx}`} strokeWidth={2} connectNulls={true} dot={false} />
                    <Line key={`hours-${idx}`} type="monotone" dataKey={hoursKey} stroke={getIndexColor(idx, idxIndex)} name={`Hours ${idx}`} strokeWidth={2} connectNulls={true} dot={false} strokeDasharray="5 5" />
                  </>
                ) : null;
              })}
            </LineChart>
          </ResponsiveContainer>

          <h3>Activity Distribution</h3>
          <ResponsiveContainer width="100%" height={330}>
            <PieChart>
              <Pie
                data={(() => {
                  const indices = getUniqueIndices(dailyActivity.data);
                  if (indices.length === 0) {
                    return [
                      { name: 'High Productivity (> 80)', value: dailyActivityData.filter(d => d.productivity > 80).length },
                      { name: 'Medium Productivity (50-80)', value: dailyActivityData.filter(d => d.productivity >= 50 && d.productivity <= 80).length },
                      { name: 'Low Productivity (< 50)', value: dailyActivityData.filter(d => d.productivity < 50).length }
                    ];
                  }
                  
                  // Group by productivity level and index
                  const productivityGroups: Record<string, Record<string, number>> = {};
                  dailyActivity.data.forEach(d => {
                    let productivityLevel = 'Low Productivity (< 50)';
                    const productivity = d.data?.productivity_score || 0;
                    if (productivity > 80) productivityLevel = 'High Productivity (> 80)';
                    else if (productivity >= 50) productivityLevel = 'Medium Productivity (50-80)';
                    
                    const sourceIndex = (d as any).sourceIndex || 'unknown';
                    
                    if (!productivityGroups[productivityLevel]) {
                      productivityGroups[productivityLevel] = {};
                    }
                    productivityGroups[productivityLevel][sourceIndex] = (productivityGroups[productivityLevel][sourceIndex] || 0) + 1;
                  });
                  
                  const result: any[] = [];
                  Object.keys(productivityGroups).forEach(productivityLevel => {
                    indices.forEach(idx => {
                      const count = productivityGroups[productivityLevel][idx] || 0;
                      if (count > 0) {
                        result.push({
                          name: `${productivityLevel} (${idx})`,
                          value: count,
                          productivityLevel: productivityLevel,
                          index: idx
                        });
                      }
                    });
                  });
                  
                  return result;
                })()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {(() => {
                  const indices = getUniqueIndices(dailyActivity.data);
                  return indices.map((idx, idxIndex) => (
                    <Cell key={`cell-${idx}`} fill={getIndexColor(idx, idxIndex)} />
                  ));
                })()}
              </Pie>
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(dailyActivity.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'High Productivity', dataKey: 'high_productivity', color: '#82ca9d' },
                      { value: 'Medium Productivity', dataKey: 'medium_productivity', color: '#ffc658' },
                      { value: 'Low Productivity', dataKey: 'low_productivity', color: '#ff6b6b' }
                    ]} onToggle={() => {}} visibilityState={{}} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Productivity Levels', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Productivity Levels (${idx})`, 
                      dataKey: `productivity_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={() => {}} visibilityState={{}} />;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );
      
      case 'comparison': return (
        <div>
          <h3>Cross-Server Comparison</h3>
          {crossServerMetricsData.length === 0 ? (
            <NoDataMessage message="No cross-server metrics data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(crossServerMetrics.data);
              
              // Group by server and index
              const serverGroups: Record<string, Record<string, any>> = {};
              
              crossServerMetrics.data.slice(0, 15).forEach(d => {
                const server = d.data?.server_id || 'Unknown';
                const sourceIndex = (d as any).sourceIndex || 'unknown';
                
                if (!serverGroups[server]) {
                  serverGroups[server] = { server };
                }
                
                // Add value for this index
                serverGroups[server][`value_${sourceIndex}`] = d.data?.value || 0;
              });
              
              return Object.values(serverGroups);
            })()}>
          <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="server" angle={-45} textAnchor="end" height={80} />
          <YAxis />
          <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(crossServerMetrics.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Metric Value', dataKey: 'value', color: '#8884d8' }
                    ]} onToggle={toggleCrossServerMetricsLineVisibility} visibilityState={crossServerMetricsVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Metric Values', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Metric Value (${idx})`, 
                      dataKey: `value_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleCrossServerMetricsLineVisibility} visibilityState={crossServerMetricsVisibleLines} />;
                }}
              />
              {getUniqueIndices(crossServerMetrics.data).map((idx, idxIndex) => {
                const valueKey = `value_${idx}`;
                const isVisible = crossServerMetricsVisibleLines[valueKey] === true || 
                                 (crossServerMetricsVisibleLines[valueKey] === undefined && Object.keys(crossServerMetricsVisibleLines).length === 0) || 
                                 crossServerMetricsVisibleLines['all'] === true;
                
                return isVisible ? (
                  <Bar key={`value-${idx}`} dataKey={valueKey} name={`Metric Value ${idx}`} fill={getIndexColor(idx, idxIndex)} />
                ) : null;
              })}
        </BarChart>
      </ResponsiveContainer>
          )}

          <h3>Server Performance Metrics</h3>
          {crossServerComparisonData.length === 0 ? (
            <NoDataMessage message="No cross-server comparison data available." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <ComposedChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(crossServerComparison.data);
              
              // Group by server and index
              const serverGroups: Record<string, Record<string, any>> = {};
              
              crossServerComparison.data.slice(0, 15).forEach(d => {
                const server = d.data?.server_id || 'Unknown';
                const sourceIndex = (d as any).sourceIndex || 'unknown';
                
                if (!serverGroups[server]) {
                  serverGroups[server] = { server };
                }
                
                // Add value and percentile for this index
                serverGroups[server][`value_${sourceIndex}`] = d.data?.value || 0;
                serverGroups[server][`percentile_${sourceIndex}`] = 0; // Default percentile value
              });
              
              return Object.values(serverGroups);
            })()}>
          <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="server" angle={-45} textAnchor="end" height={80} />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(crossServerComparison.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Comparison Value', dataKey: 'value', color: '#8884d8' },
                      { value: 'Percentile Rank', dataKey: 'percentile', color: '#82ca9d' }
                    ]} onToggle={toggleCrossServerLineVisibility} visibilityState={crossServerVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Comparison Values', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Comparison Value (${idx})`, 
                      dataKey: `value_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleCrossServerLineVisibility} visibilityState={crossServerVisibleLines} />;
                }}
              />
              {getUniqueIndices(crossServerComparison.data).map((idx, idxIndex) => {
                const valueKey = `value_${idx}`;
                const percentileKey = `percentile_${idx}`;
                const isVisible = crossServerVisibleLines[valueKey] === true || 
                                 (crossServerVisibleLines[valueKey] === undefined && Object.keys(crossServerVisibleLines).length === 0) || 
                                 crossServerVisibleLines['all'] === true;
                
                return isVisible ? (
                  <>
                    <Bar key={`value-${idx}`} yAxisId="left" dataKey={valueKey} name={`Comparison Value ${idx}`} fill={getIndexColor(idx, idxIndex)} />
                    <Line key={`percentile-${idx}`} yAxisId="right" type="monotone" dataKey={percentileKey} stroke={getIndexColor(idx, idxIndex)} name={`Percentile Rank ${idx}`} strokeWidth={2} connectNulls={true} dot={false} />
                  </>
                ) : null;
              })}
            </ComposedChart>
          </ResponsiveContainer>
          )}

          <h3>Metric Distribution</h3>
          {crossServerMetricsData.length === 0 ? (
            <NoDataMessage message="No server performance data available." />
          ) : (
          <ResponsiveContainer width="100%" height={330}>
            <PieChart>
              <Pie
                data={(() => {
                  const indices = getUniqueIndices(crossServerMetrics.data);
                  if (indices.length === 0) {
                    return Object.entries(
                      crossServerMetricsData.reduce((acc: any, metric) => {
                        acc[metric.server] = (acc[metric.server] || 0) + metric.value;
                        return acc;
                      }, {} as Record<string, number>)
                    ).map(([server, value]) => ({ name: server, value: value }));
                  }
                  
                  // Group by server and index
                  const serverGroups: Record<string, Record<string, number>> = {};
                  crossServerMetrics.data.forEach(d => {
                    const server = d.data?.server_id || 'Unknown';
                    const sourceIndex = (d as any).sourceIndex || 'unknown';
                    const value = d.data?.value || 0;
                    
                    if (!serverGroups[server]) {
                      serverGroups[server] = {};
                    }
                    serverGroups[server][sourceIndex] = (serverGroups[server][sourceIndex] || 0) + value;
                  });
                  
                  const result: any[] = [];
                  Object.keys(serverGroups).forEach(server => {
                    indices.forEach(idx => {
                      const value = serverGroups[server][idx] || 0;
                      if (value > 0) {
                        result.push({
                          name: `${server} (${idx})`,
                          value: value,
                          server: server,
                          index: idx
                        });
                      }
                    });
                  });
                  
                  return result;
                })()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {(() => {
                  const indices = getUniqueIndices(crossServerMetrics.data);
                  return indices.map((idx, idxIndex) => (
                    <Cell key={`cell-${idx}`} fill={getIndexColor(idx, idxIndex)} />
                  ));
                })()}
              </Pie>
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(crossServerMetrics.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Server A', dataKey: 'server_a', color: '#8884d8' },
                      { value: 'Server B', dataKey: 'server_b', color: '#82ca9d' },
                      { value: 'Server C', dataKey: 'server_c', color: '#ffc658' }
                    ]} onToggle={() => {}} visibilityState={{}} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Servers', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Servers (${idx})`, 
                      dataKey: `server_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={() => {}} visibilityState={{}} />;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          )}
        </div>
      );
      
      case 'security': return (
        <div>
          <h3>Security Risk Assessment</h3>
          <ResponsiveContainer width="100%" height={330}>
            <ComposedChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(cmds.data);
              
              // Group by user and index
              const userGroups: Record<string, Record<string, any>> = {};
              
              securityData.slice(0, 10).forEach((s: any) => {
                const user = s.user || 'Unknown';
                const sourceIndex = 'unknown'; // securityData doesn't have sourceIndex, using default
                
                if (!userGroups[user]) {
                  userGroups[user] = { user };
                }
                
                // Add risk and factors for this index
                userGroups[user][`risk_${sourceIndex}`] = s.risk || 0;
                userGroups[user][`factors_${sourceIndex}`] = s.factors || 0;
              });
              
              return Object.values(userGroups);
            })()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="user" angle={-45} textAnchor="end" height={80} />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(cmds.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Risk Score', dataKey: 'risk', color: '#ff6b6b' },
                      { value: 'Risk Factors', dataKey: 'factors', color: '#ffc658' }
                    ]} onToggle={toggleCommandSecurityLineVisibility} visibilityState={commandSecurityVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Risk Scores', dataKey: 'all', color: '#ff6b6b' },
                    ...indices.map((idx, i) => ({ 
                      value: `Risk Score (${idx})`, 
                      dataKey: `risk_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleCommandSecurityLineVisibility} visibilityState={commandSecurityVisibleLines} />;
                }}
              />
              {getUniqueIndices(cmds.data).map((idx, idxIndex) => {
                const riskKey = `risk_${idx}`;
                const factorsKey = `factors_${idx}`;
                const isVisible = commandSecurityVisibleLines[riskKey] === true || 
                                 (commandSecurityVisibleLines[riskKey] === undefined && Object.keys(commandSecurityVisibleLines).length === 0) || 
                                 commandSecurityVisibleLines['all'] === true;
                
                return isVisible ? (
                  <>
                    <Bar key={`risk-${idx}`} yAxisId="left" dataKey={riskKey} name={`Risk Score ${idx}`} fill={getIndexColor(idx, idxIndex)} />
                    <Line key={`factors-${idx}`} yAxisId="right" type="monotone" dataKey={factorsKey} stroke={getIndexColor(idx, idxIndex)} name={`Risk Factors ${idx}`} strokeWidth={2} connectNulls={true} dot={false} />
                  </>
                ) : null;
              })}
            </ComposedChart>
          </ResponsiveContainer>

          <h3>Risk Level Distribution</h3>
          <ResponsiveContainer width="100%" height={330}>
            <PieChart>
              <Pie
                data={(() => {
                  const indices = getUniqueIndices(cmds.data);
                  if (indices.length === 0) {
                    return [
                      { name: 'High Risk (> 80)', value: securityData.filter((s: any) => s.risk > 80).length },
                      { name: 'Medium Risk (50-80)', value: securityData.filter((s: any) => s.risk >= 50 && s.risk <= 80).length },
                      { name: 'Low Risk (< 50)', value: securityData.filter((s: any) => s.risk < 50).length }
                    ];
                  }
                  
                  // Group by risk level and index
                  const riskGroups: Record<string, Record<string, number>> = {};
                  securityData.forEach((s: any) => {
                    let riskLevel = 'Low Risk (< 50)';
                    if (s.risk > 80) riskLevel = 'High Risk (> 80)';
                    else if (s.risk >= 50) riskLevel = 'Medium Risk (50-80)';
                    
                    const sourceIndex = 'unknown'; // securityData doesn't have sourceIndex
                    
                    if (!riskGroups[riskLevel]) {
                      riskGroups[riskLevel] = {};
                    }
                    riskGroups[riskLevel][sourceIndex] = (riskGroups[riskLevel][sourceIndex] || 0) + 1;
                  });
                  
                  const result: any[] = [];
                  Object.keys(riskGroups).forEach(riskLevel => {
                    indices.forEach(idx => {
                      const count = riskGroups[riskLevel][idx] || 0;
                      if (count > 0) {
                        result.push({
                          name: `${riskLevel} (${idx})`,
                          value: count,
                          riskLevel: riskLevel,
                          index: idx
                        });
                      }
                    });
                  });
                  
                  return result;
                })()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#ff6b6b"
                dataKey="value"
              >
                {(() => {
                  const indices = getUniqueIndices(cmds.data);
                  return indices.map((idx, idxIndex) => (
                    <Cell key={`cell-${idx}`} fill={getIndexColor(idx, idxIndex)} />
                  ));
                })()}
              </Pie>
              <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(cmds.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'High Risk', dataKey: 'high_risk', color: '#ff6b6b' },
                      { value: 'Medium Risk', dataKey: 'medium_risk', color: '#ffc658' },
                      { value: 'Low Risk', dataKey: 'low_risk', color: '#82ca9d' }
                    ]} onToggle={() => {}} visibilityState={{}} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Risk Levels', dataKey: 'all', color: '#ff6b6b' },
                    ...indices.map((idx, i) => ({ 
                      value: `Risk Levels (${idx})`, 
                      dataKey: `risk_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={() => {}} visibilityState={{}} />;
                }}
              />
            </PieChart>
          </ResponsiveContainer>

          <h3>Session Security Analysis</h3>
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={(() => {
              // Process data to support multi-index structure
              const indices = getUniqueIndices(cmds.data);
              
              // Group by user and index
              const userGroups: Record<string, Record<string, any>> = {};
              
              securityData.forEach((s: any) => {
                const user = s.user || 'Unknown';
                const sourceIndex = 'unknown'; // securityData doesn't have sourceIndex
                
                if (!userGroups[user]) {
                  userGroups[user] = { user };
                }
                
                // Add sessions and risk for this index
                userGroups[user][`sessions_${sourceIndex}`] = s.sessions || 0;
                userGroups[user][`risk_${sourceIndex}`] = s.risk || 0;
              });
              
              return Object.values(userGroups);
            })()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="user" angle={-45} textAnchor="end" height={80} />
          <YAxis />
          <Tooltip />
              <Legend 
                content={() => {
                  const indices = getUniqueIndices(cmds.data);
                  if (indices.length === 0) {
                    return <CustomLegend payload={[
                      { value: 'Sessions', dataKey: 'sessions', color: '#8884d8' },
                      { value: 'Risk Score', dataKey: 'risk', color: '#ff6b6b' }
                    ]} onToggle={toggleCommandSecurityLineVisibility} visibilityState={commandSecurityVisibleLines} />;
                  }
                  const colors = indices.map((_, idxIndex) => getIndexColor(indices[idxIndex], idxIndex));
                  const payload = [
                    { value: 'All Sessions', dataKey: 'all', color: '#8884d8' },
                    ...indices.map((idx, i) => ({ 
                      value: `Sessions (${idx})`, 
                      dataKey: `sessions_${idx}`, 
                      color: colors[i] 
                    }))
                  ];
                  return <CustomLegend payload={payload} onToggle={toggleCommandSecurityLineVisibility} visibilityState={commandSecurityVisibleLines} />;
                }}
              />
              {getUniqueIndices(cmds.data).map((idx, idxIndex) => {
                const sessionsKey = `sessions_${idx}`;
                const riskKey = `risk_${idx}`;
                const isVisible = commandSecurityVisibleLines[sessionsKey] === true || 
                                 (commandSecurityVisibleLines[sessionsKey] === undefined && Object.keys(commandSecurityVisibleLines).length === 0) || 
                                 commandSecurityVisibleLines['all'] === true;
                
                return isVisible ? (
                  <>
                    <Bar key={`sessions-${idx}`} dataKey={sessionsKey} name={`Sessions ${idx}`} fill={getIndexColor(idx, idxIndex)} />
                    <Bar key={`risk-${idx}`} dataKey={riskKey} name={`Risk Score ${idx}`} fill={getIndexColor(idx, idxIndex)} opacity={0.7} />
                  </>
                ) : null;
              })}
        </BarChart>
      </ResponsiveContainer>
        </div>
      );

      case 'developer': return (
        <div>
          <h2 style={{ marginBottom: 24, color: '#333' }}>💻 Developer Insights</h2>
          <p style={{ color: '#666', marginBottom: 32 }}>Comprehensive monitoring of development activities, code quality, and environment usage</p>

          {/* FileSystem Monitor */}
          <h3>📁 File System Activity</h3>
          {filesystemData.data.length === 0 ? (
            <NoDataMessage message="No filesystem activity data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <LineChart data={filesystemData.data.map(d => ({
                  time: new Date(d.timestamp).toLocaleString(),
                  created: d.data?.files_created || 0,
                  modified: d.data?.files_modified || 0,
                  deleted: d.data?.files_deleted || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="created" stroke="#82ca9d" strokeWidth={2} name="Files Created" dot={false} />
                  <Line type="monotone" dataKey="modified" stroke="#8884d8" strokeWidth={2} name="Files Modified" dot={false} />
                  <Line type="monotone" dataKey="deleted" stroke="#ff6b6b" strokeWidth={2} name="Files Deleted" dot={false} />
                </LineChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <PieChart>
                  <Pie
                    data={(() => {
                      const langs: Record<string, number> = {};
                      filesystemData.data.forEach(d => {
                        const languages = d.data?.languages || {};
                        Object.entries(languages).forEach(([lang, count]) => {
                          langs[lang] = (langs[lang] || 0) + (count as number);
                        });
                      });
                      return Object.entries(langs).map(([name, value]) => ({ name, value }));
                    })()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                  >
                    {Object.keys(filesystemData.data.reduce((acc: any, d) => {
                      const languages = d.data?.languages || {};
                      return { ...acc, ...languages };
                    }, {})).map((_, idx) => (
                      <Cell key={`cell-${idx}`} fill={getIndexColor(idx.toString(), idx)} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Error/Debug Monitor */}
          <h3 style={{ marginTop: 40 }}>🐛 Error & Debug Tracking</h3>
          {errorDebugData.data.length === 0 ? (
            <NoDataMessage message="No error/debug data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <LineChart data={errorDebugData.data.map(d => ({
                  time: new Date(d.timestamp).toLocaleString(),
                  errors: d.data?.error_count || 0,
                  debugSessions: d.data?.debug_sessions || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="errors" stroke="#ff6b6b" strokeWidth={2} name="Error Count" dot={false} />
                  <Line type="monotone" dataKey="debugSessions" stroke="#ffc658" strokeWidth={2} name="Debug Sessions" dot={false} />
                </LineChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={errorDebugData.data.slice(-20).map(d => ({
                  type: d.data?.error_type || 'Unknown',
                  resolution: d.data?.resolution_time_minutes || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="resolution" fill="#ff6b6b" name="Resolution Time (min)" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Dev Environment Monitor */}
          <h3 style={{ marginTop: 40 }}>🛠️ Development Environment</h3>
          {devEnvironmentData.data.length === 0 ? (
            <NoDataMessage message="No development environment data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <PieChart>
                  <Pie
                    data={(() => {
                      const ides: Record<string, number> = {};
                      devEnvironmentData.data.forEach(d => {
                        const ide = d.data?.ide_name || 'Unknown';
                        const usage = d.data?.usage_minutes || 0;
                        ides[ide] = (ides[ide] || 0) + usage;
                      });
                      return Object.entries(ides).map(([name, value]) => ({ name, value }));
                    })()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                  >
                    {Object.keys(devEnvironmentData.data.reduce((acc: any, d) => {
                      return { ...acc, [d.data?.ide_name || 'Unknown']: 1 };
                    }, {})).map((_, idx) => (
                      <Cell key={`cell-${idx}`} fill={getIndexColor(idx.toString(), idx)} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={devEnvironmentData.data.slice(-15).map(d => ({
                  ide: d.data?.ide_name || 'Unknown',
                  usage: d.data?.usage_minutes || 0,
                  plugins: d.data?.plugins?.length || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ide" angle={-45} textAnchor="end" height={80} />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="usage" fill="#8884d8" name="Usage (min)" />
                  <Bar yAxisId="right" dataKey="plugins" fill="#82ca9d" name="Plugin Count" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Browser Activity Monitor */}
          <h3 style={{ marginTop: 40 }}>🌐 Browser Activity</h3>
          {browserActivityData.data.length === 0 ? (
            <NoDataMessage message="No browser activity data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <PieChart>
                  <Pie
                    data={(() => {
                      let educational = 0, nonEducational = 0;
                      browserActivityData.data.forEach(d => {
                        const duration = d.data?.duration_minutes || 0;
                        if (d.data?.is_educational) educational += duration;
                        else nonEducational += duration;
                      });
                      return [
                        { name: 'Educational', value: educational },
                        { name: 'Non-Educational', value: nonEducational }
                      ];
                    })()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                  >
                    <Cell fill="#82ca9d" />
                    <Cell fill="#ff6b6b" />
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={(() => {
                  const categories: Record<string, number> = {};
                  browserActivityData.data.forEach(d => {
                    const cat = d.data?.site_category || 'Unknown';
                    const dur = d.data?.duration_minutes || 0;
                    categories[cat] = (categories[cat] || 0) + dur;
                  });
                  return Object.entries(categories).slice(0, 15).map(([name, value]) => ({ name, value }));
                })()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#8884d8" name="Duration (min)" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Code Quality Monitor */}
          <h3 style={{ marginTop: 40 }}>✅ Code Quality Metrics</h3>
          {codeQualityData.data.length === 0 ? (
            <NoDataMessage message="No code quality data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <LineChart data={codeQualityData.data.map(d => ({
                  time: new Date(d.timestamp).toLocaleString(),
                  quality: d.data?.quality_score || 0,
                  coverage: d.data?.test_coverage || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="quality" stroke="#82ca9d" strokeWidth={2} name="Quality Score" dot={false} />
                  <Line type="monotone" dataKey="coverage" stroke="#8884d8" strokeWidth={2} name="Test Coverage %" dot={false} />
                </LineChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={codeQualityData.data.slice(-15).map(d => ({
                  file: (d.data?.file_path || 'Unknown').split('/').pop() || 'Unknown',
                  functions: d.data?.function_count || 0,
                  complexity: d.data?.complexity_score || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="file" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="functions" fill="#8884d8" name="Function Count" />
                  <Bar dataKey="complexity" fill="#ffc658" name="Complexity Score" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Package Dependency Monitor */}
          <h3 style={{ marginTop: 40 }}>📦 Package Dependencies</h3>
          {packageDependencyData.data.length === 0 ? (
            <NoDataMessage message="No package dependency data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={packageDependencyData.data.slice(-20).map(d => ({
                  package: d.data?.package_name || 'Unknown',
                  deps: d.data?.dependency_count || 0,
                  time: new Date(d.data?.install_time || d.timestamp).toLocaleTimeString()
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="package" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="deps" fill="#8884d8" name="Dependency Count" />
                </BarChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <PieChart>
                  <Pie
                    data={(() => {
                      let conflicts = 0, noConflicts = 0;
                      packageDependencyData.data.forEach(d => {
                        if (d.data?.has_conflicts) conflicts++;
                        else noConflicts++;
                      });
                      return [
                        { name: 'With Conflicts', value: conflicts },
                        { name: 'No Conflicts', value: noConflicts }
                      ];
                    })()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                  >
                    <Cell fill="#ff6b6b" />
                    <Cell fill="#82ca9d" />
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Collaboration Monitor */}
          <h3 style={{ marginTop: 40 }}>🤝 Collaboration Activities</h3>
          {collaborationData.data.length === 0 ? (
            <NoDataMessage message="No collaboration data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <PieChart>
                  <Pie
                    data={(() => {
                      const types: Record<string, number> = {};
                      collaborationData.data.forEach(d => {
                        const type = d.data?.collaboration_type || 'Unknown';
                        types[type] = (types[type] || 0) + 1;
                      });
                      return Object.entries(types).map(([name, value]) => ({ name, value }));
                    })()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                  >
                    {Object.keys(collaborationData.data.reduce((acc: any, d) => {
                      return { ...acc, [d.data?.collaboration_type || 'Unknown']: 1 };
                    }, {})).map((_, idx) => (
                      <Cell key={`cell-${idx}`} fill={getIndexColor(idx.toString(), idx)} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={collaborationData.data.slice(-15).map(d => ({
                  type: d.data?.collaboration_type || 'Unknown',
                  participants: d.data?.participants || 0,
                  duration: d.data?.duration_minutes || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" angle={-45} textAnchor="end" height={80} />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="participants" fill="#8884d8" name="Participants" />
                  <Bar yAxisId="right" dataKey="duration" fill="#82ca9d" name="Duration (min)" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Learning Path Monitor */}
          <h3 style={{ marginTop: 40 }}>🎓 Learning Path Progress</h3>
          {learningPathData.data.length === 0 ? (
            <NoDataMessage message="No learning path data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <LineChart data={learningPathData.data.map(d => ({
                  time: new Date(d.timestamp).toLocaleString(),
                  completion: d.data?.completion_percent || 0,
                  quizScore: d.data?.quiz_score || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="completion" stroke="#82ca9d" strokeWidth={2} name="Completion %" dot={false} />
                  <Line type="monotone" dataKey="quizScore" stroke="#8884d8" strokeWidth={2} name="Quiz Score" dot={false} />
                </LineChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={learningPathData.data.slice(-15).map(d => ({
                  item: d.data?.exercise_name || d.data?.assignment_name || d.data?.milestone || 'Unknown',
                  score: d.data?.quiz_score || d.data?.completion_percent || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="item" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="score" fill="#82ca9d" name="Score/Progress" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Resource Access Monitor */}
          <h3 style={{ marginTop: 40 }}>🔌 Resource Access</h3>
          {resourceAccessData.data.length === 0 ? (
            <NoDataMessage message="No resource access data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <PieChart>
                  <Pie
                    data={(() => {
                      const types: Record<string, number> = {};
                      resourceAccessData.data.forEach(d => {
                        const type = d.data?.resource_type || 'Unknown';
                        const count = d.data?.access_count || 1;
                        types[type] = (types[type] || 0) + count;
                      });
                      return Object.entries(types).map(([name, value]) => ({ name, value }));
                    })()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                  >
                    {Object.keys(resourceAccessData.data.reduce((acc: any, d) => {
                      return { ...acc, [d.data?.resource_type || 'Unknown']: 1 };
                    }, {})).map((_, idx) => (
                      <Cell key={`cell-${idx}`} fill={getIndexColor(idx.toString(), idx)} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <LineChart data={resourceAccessData.data.map(d => ({
                  time: new Date(d.timestamp).toLocaleString(),
                  transferred: d.data?.data_transferred_mb || 0,
                  responseTime: d.data?.response_time_ms || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="transferred" stroke="#8884d8" strokeWidth={2} name="Data Transferred (MB)" dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="responseTime" stroke="#ffc658" strokeWidth={2} name="Response Time (ms)" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Time Distribution Analyzer */}
          <h3 style={{ marginTop: 40 }}>⏰ Time Distribution</h3>
          {timeDistributionData.data.length === 0 ? (
            <NoDataMessage message="No time distribution data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <PieChart>
                  <Pie
                    data={(() => {
                      const activities: Record<string, number> = {};
                      timeDistributionData.data.forEach(d => {
                        const activity = d.data?.activity_type || 'Unknown';
                        const duration = d.data?.duration_minutes || 0;
                        activities[activity] = (activities[activity] || 0) + duration;
                      });
                      return Object.entries(activities).map(([name, value]) => ({ name, value }));
                    })()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                  >
                    {Object.keys(timeDistributionData.data.reduce((acc: any, d) => {
                      return { ...acc, [d.data?.activity_type || 'Unknown']: 1 };
                    }, {})).map((_, idx) => (
                      <Cell key={`cell-${idx}`} fill={getIndexColor(idx.toString(), idx)} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <LineChart data={timeDistributionData.data.map(d => ({
                  time: new Date(d.timestamp).toLocaleString(),
                  contextSwitches: d.data?.context_switches || 0,
                  focusScore: d.data?.focus_score || 0,
                  productivity: d.data?.productivity_score || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="contextSwitches" stroke="#ff6b6b" strokeWidth={2} name="Context Switches" dot={false} />
                  <Line type="monotone" dataKey="focusScore" stroke="#82ca9d" strokeWidth={2} name="Focus Score" dot={false} />
                  <Line type="monotone" dataKey="productivity" stroke="#8884d8" strokeWidth={2} name="Productivity" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Hardware Utilization Monitor */}
          <h3 style={{ marginTop: 40 }}>🖥️ Hardware Utilization</h3>
          {hardwareUtilizationData.data.length === 0 ? (
            <NoDataMessage message="No hardware utilization data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <LineChart data={hardwareUtilizationData.data.map(d => ({
                  time: new Date(d.timestamp).toLocaleString(),
                  gpu: d.data?.gpu_utilization || 0,
                  gpuMemory: d.data?.gpu_memory_used_mb || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="gpu" stroke="#8884d8" strokeWidth={2} name="GPU Utilization %" dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="gpuMemory" stroke="#82ca9d" strokeWidth={2} name="GPU Memory (MB)" dot={false} />
                </LineChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={(() => {
                  const peripherals: Record<string, number> = {};
                  hardwareUtilizationData.data.forEach(d => {
                    const type = d.data?.peripheral_type || 'Unknown';
                    const usage = d.data?.peripheral_usage_minutes || 0;
                    peripherals[type] = (peripherals[type] || 0) + usage;
                  });
                  return Object.entries(peripherals).map(([name, value]) => ({ name, value }));
                })()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#8884d8" name="Usage (min)" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Network Behavior Monitor */}
          <h3 style={{ marginTop: 40 }}>🌐 Network Behavior</h3>
          {networkBehaviorData.data.length === 0 ? (
            <NoDataMessage message="No network behavior data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <LineChart data={networkBehaviorData.data.map(d => ({
                  time: new Date(d.timestamp).toLocaleString(),
                  transferred: (d.data?.bytes_transferred || 0) / (1024 * 1024),
                  bandwidth: d.data?.bandwidth_mbps || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="transferred" stroke="#8884d8" strokeWidth={2} name="Data Transferred (MB)" dot={false} />
                  <Line type="monotone" dataKey="bandwidth" stroke="#82ca9d" strokeWidth={2} name="Bandwidth (Mbps)" dot={false} />
                </LineChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={(() => {
                  const repos: Record<string, number> = {};
                  networkBehaviorData.data.forEach(d => {
                    const repo = d.data?.repository || 'Unknown';
                    repos[repo] = (repos[repo] || 0) + 1;
                  });
                  return Object.entries(repos).slice(0, 15).map(([name, value]) => ({ name, value }));
                })()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#8884d8" name="Access Count" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Terminal/Console Analyzer */}
          <h3 style={{ marginTop: 40 }}>💬 Terminal & Console Activity</h3>
          {terminalConsoleData.data.length === 0 ? (
            <NoDataMessage message="No terminal/console data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <PieChart>
                  <Pie
                    data={(() => {
                      const categories: Record<string, number> = {};
                      terminalConsoleData.data.forEach(d => {
                        const cat = d.data?.command_category || 'Unknown';
                        categories[cat] = (categories[cat] || 0) + 1;
                      });
                      return Object.entries(categories).map(([name, value]) => ({ name, value }));
                    })()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                  >
                    {Object.keys(terminalConsoleData.data.reduce((acc: any, d) => {
                      return { ...acc, [d.data?.command_category || 'Unknown']: 1 };
                    }, {})).map((_, idx) => (
                      <Cell key={`cell-${idx}`} fill={getIndexColor(idx.toString(), idx)} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <LineChart data={terminalConsoleData.data.map(d => ({
                  time: new Date(d.timestamp).toLocaleString(),
                  proficiency: d.data?.proficiency_score || 0,
                  executionTime: d.data?.execution_time_ms || 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="proficiency" stroke="#82ca9d" strokeWidth={2} name="Proficiency Score" dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="executionTime" stroke="#ffc658" strokeWidth={2} name="Execution Time (ms)" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </>
          )}

          {/* Project Lifecycle Monitor */}
          <h3 style={{ marginTop: 40 }}>🚀 Project Lifecycle</h3>
          {projectLifecycleData.data.length === 0 ? (
            <NoDataMessage message="No project lifecycle data available" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={330}>
                <PieChart>
                  <Pie
                    data={(() => {
                      const stages: Record<string, number> = {};
                      projectLifecycleData.data.forEach(d => {
                        const stage = d.data?.lifecycle_stage || 'Unknown';
                        stages[stage] = (stages[stage] || 0) + 1;
                      });
                      return Object.entries(stages).map(([name, value]) => ({ name, value }));
                    })()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                  >
                    {Object.keys(projectLifecycleData.data.reduce((acc: any, d) => {
                      return { ...acc, [d.data?.lifecycle_stage || 'Unknown']: 1 };
                    }, {})).map((_, idx) => (
                      <Cell key={`cell-${idx}`} fill={getIndexColor(idx.toString(), idx)} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={projectLifecycleData.data.slice(-15).map(d => ({
                  project: d.data?.project_name || 'Unknown',
                  duration: d.data?.stage_duration_minutes || 0,
                  errors: d.data?.error_count || 0,
                  success: d.data?.success ? 1 : 0
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="project" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="duration" fill="#8884d8" name="Duration (min)" />
                  <Bar dataKey="errors" fill="#ff6b6b" name="Error Count" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          <div style={{ marginTop: 40, padding: 16, backgroundColor: '#f9f9f9', borderRadius: 8 }}>
            <h4>Developer Insights Summary</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
              <div>📁 Filesystem Events: {filesystemData.data.length}</div>
              <div>🐛 Error Records: {errorDebugData.data.length}</div>
              <div>🛠️ IDE Sessions: {devEnvironmentData.data.length}</div>
              <div>🌐 Browser Activities: {browserActivityData.data.length}</div>
              <div>✅ Code Quality Checks: {codeQualityData.data.length}</div>
              <div>📦 Package Operations: {packageDependencyData.data.length}</div>
              <div>🤝 Collaborations: {collaborationData.data.length}</div>
              <div>🎓 Learning Activities: {learningPathData.data.length}</div>
              <div>🔌 Resource Accesses: {resourceAccessData.data.length}</div>
              <div>⏰ Time Entries: {timeDistributionData.data.length}</div>
              <div>🖥️ Hardware Records: {hardwareUtilizationData.data.length}</div>
              <div>🌐 Network Events: {networkBehaviorData.data.length}</div>
              <div>💬 Terminal Commands: {terminalConsoleData.data.length}</div>
              <div>🚀 Project Stages: {projectLifecycleData.data.length}</div>
            </div>
          </div>
        </div>
      );

      default: return (
        <div>
          <h3>Overview</h3>
          <NoDataMessage message="No performance data available for the selected time range" />
        </div>
      );
    }
  };

  return (
    <div ref={dashboardRef} style={{ fontFamily: 'sans-serif', padding: 16 }} className={darkMode ? 'dark-mode' : ''}>
      {/* Loading Overlay */}
      {isGeneratingPDF && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: darkMode ? 'rgba(26, 26, 26, 0.95)' : 'rgba(255, 255, 255, 0.95)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            fontSize: '18px',
            fontWeight: 'bold',
            color: darkMode ? '#e0e0e0' : '#333',
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '3em', marginBottom: 16 }}>⏳</div>
            <div>Generating PDF...</div>
            <div style={{ fontSize: '14px', marginTop: 8, opacity: 0.7 }}>
              Please wait while we prepare your download
            </div>
          </div>
        </div>
      )}

      {/* Loading Skeleton - shown while data is loading */}
      {isLoading && !isGeneratingPDF && <LoadingSkeleton />}

      {/* Alert Panel */}
      <AlertPanel />

      {/* Main Content - hidden when loading */}
      <div style={{ display: isLoading && !isGeneratingPDF ? 'none' : 'block' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
      <h2>Enhanced Monitor Dashboard</h2>
          <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
            Timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <select
            value={index}
            onChange={(e) => setIndex(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 4, border: '1px solid #ddd' }}
            disabled={loadingIndices}
          >
            {loadingIndices ? (
              <option value="">Loading indices...</option>
            ) : (
              availableIndices.map((idx) => (
                <option key={idx} value={idx}>
                  {idx === 'all' ? 'All' : idx}
                </option>
              ))
            )}
          </select>
          
          <div style={{ display: 'flex', gap: 8 }}>
            <button 
              onClick={() => handleTimePresetChange('1h')}
              style={{
                padding: '8px 16px',
                backgroundColor: selectedTimePreset === '1h' ? '#007bff' : '#f5f5f5',
                color: selectedTimePreset === '1h' ? 'white' : 'black',
                border: selectedTimePreset === '1h' ? '1px solid #007bff' : '1px solid #ddd',
                borderRadius: 4,
                cursor: 'pointer',
                fontWeight: selectedTimePreset === '1h' ? 'bold' : 'normal',
              }}
            >
              1h
            </button>
            <button 
              onClick={() => handleTimePresetChange('2h')}
              style={{
                padding: '8px 16px',
                backgroundColor: selectedTimePreset === '2h' ? '#007bff' : '#f5f5f5',
                color: selectedTimePreset === '2h' ? 'white' : 'black',
                border: selectedTimePreset === '2h' ? '1px solid #007bff' : '1px solid #ddd',
                borderRadius: 4,
                cursor: 'pointer',
                fontWeight: selectedTimePreset === '2h' ? 'bold' : 'normal',
              }}
            >
              2h
            </button>
            <button 
              onClick={() => handleTimePresetChange('6h')}
              style={{
                padding: '8px 16px',
                backgroundColor: selectedTimePreset === '6h' ? '#007bff' : '#f5f5f5',
                color: selectedTimePreset === '6h' ? 'white' : 'black',
                border: selectedTimePreset === '6h' ? '1px solid #007bff' : '1px solid #ddd',
                borderRadius: 4,
                cursor: 'pointer',
                fontWeight: selectedTimePreset === '6h' ? 'bold' : 'normal',
              }}
            >
              6h
            </button>
            <button 
              onClick={() => handleTimePresetChange('1d')}
              style={{
                padding: '8px 16px',
                backgroundColor: selectedTimePreset === '1d' ? '#007bff' : '#f5f5f5',
                color: selectedTimePreset === '1d' ? 'white' : 'black',
                border: selectedTimePreset === '1d' ? '1px solid #007bff' : '1px solid #ddd',
                borderRadius: 4,
                cursor: 'pointer',
                fontWeight: selectedTimePreset === '1d' ? 'bold' : 'normal',
              }}
            >
              1d
            </button>
            <button 
              onClick={() => handleTimePresetChange('7d')}
              style={{
                padding: '8px 16px',
                backgroundColor: selectedTimePreset === '7d' ? '#007bff' : '#f5f5f5',
                color: selectedTimePreset === '7d' ? 'white' : 'black',
                border: selectedTimePreset === '7d' ? '1px solid #007bff' : '1px solid #ddd',
                borderRadius: 4,
                cursor: 'pointer',
                fontWeight: selectedTimePreset === '7d' ? 'bold' : 'normal',
              }}
            >
              7d
            </button>
            <button 
              onClick={() => handleTimePresetChange('30d')}
              style={{
                padding: '8px 16px',
                backgroundColor: selectedTimePreset === '30d' ? '#007bff' : '#f5f5f5',
                color: selectedTimePreset === '30d' ? 'white' : 'black',
                border: selectedTimePreset === '30d' ? '1px solid #007bff' : '1px solid #ddd',
                borderRadius: 4,
                cursor: 'pointer',
                fontWeight: selectedTimePreset === '30d' ? 'bold' : 'normal',
              }}
            >
              30d
            </button>
            <button 
              onClick={() => {
                setShowCustomDateFilter(!showCustomDateFilter);
                if (!showCustomDateFilter) {
                  setSelectedTimePreset('custom');
                }
              }}
              style={{
                padding: '8px 16px',
                backgroundColor: selectedTimePreset === 'custom' ? '#007bff' : '#f5f5f5',
                color: selectedTimePreset === 'custom' ? 'white' : 'black',
                border: selectedTimePreset === 'custom' ? '1px solid #007bff' : '1px solid #ddd',
                borderRadius: 4,
                cursor: 'pointer',
                fontWeight: selectedTimePreset === 'custom' ? 'bold' : 'normal',
              }}
            >
              📅 Custom
            </button>
          </div>

          {/* Custom Date Filter */}
          {showCustomDateFilter && (
            <div style={{ 
              marginTop: 12, 
              padding: 16, 
              backgroundColor: '#f9f9f9', 
              borderRadius: 8, 
              border: '1px solid #ddd',
              display: 'flex',
              gap: 16,
              alignItems: 'center',
              flexWrap: 'wrap'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#666' }}>
                  Start Date & Time
                </label>
                <input
                  type="datetime-local"
                  value={dateRange.start}
                  onChange={(e) => handleCustomDateChange('start', e.target.value)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 4,
                    border: '1px solid #ddd',
                    fontSize: '14px'
                  }}
                />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#666' }}>
                  End Date & Time
                </label>
                <input
                  type="datetime-local"
                  value={dateRange.end}
                  onChange={(e) => handleCustomDateChange('end', e.target.value)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 4,
                    border: '1px solid #ddd',
                    fontSize: '14px'
                  }}
                />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#666' }}>
                  Quick Actions
                </label>
                <div style={{ fontSize: '10px', color: '#888', marginBottom: 4 }}>
                  Timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => {
                      const now = new Date();
                      const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
                      setDateRange({
                        start: formatDateForInput(oneHourAgo),
                        end: formatDateForInput(now)
                      });
                    }}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#e3f2fd',
                      border: '1px solid #2196f3',
                      borderRadius: 4,
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    Last Hour
                  </button>
                  <button
                    onClick={() => {
                      const now = new Date();
                      const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                      setDateRange({
                        start: formatDateForInput(oneDayAgo),
                        end: formatDateForInput(now)
                      });
                    }}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#e8f5e8',
                      border: '1px solid #4caf50',
                      borderRadius: 4,
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    Last Day
                  </button>
                  <button
                    onClick={() => {
                      const now = new Date();
                      const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                      setDateRange({
                        start: formatDateForInput(oneWeekAgo),
                        end: formatDateForInput(now)
                      });
                    }}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#fff3e0',
                      border: '1px solid #ff9800',
                      borderRadius: 4,
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    Last Week
                  </button>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={downloadPDF}
            disabled={isGeneratingPDF}
            className="pdf-button"
            style={{
              padding: '8px 16px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: isGeneratingPDF ? 'not-allowed' : 'pointer',
              opacity: isGeneratingPDF ? 0.6 : 1,
            }}
          >
            📄 Download PDF
          </button>

          <button
            onClick={exportChartsAsPNG}
            disabled={isGeneratingPDF}
            style={{
              padding: '8px 16px',
              backgroundColor: '#2196f3',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: isGeneratingPDF ? 'not-allowed' : 'pointer',
              opacity: isGeneratingPDF ? 0.6 : 1,
            }}
            title="Export all charts in current tab as PNG files"
          >
            🖼️ Export Charts
          </button>

          <button
            onClick={exportCurrentTabData}
            style={{
              padding: '8px 16px',
              backgroundColor: '#ff9800',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
            }}
            title="Export current tab data as CSV"
          >
            📊 Export CSV
          </button>

          <button
            onClick={copyShareableLink}
            style={{
              padding: '8px 16px',
              backgroundColor: '#9c27b0',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
            }}
            title="Copy shareable link with current dashboard state"
          >
            🔗 Share
          </button>

          <button
            onClick={() => setShowAlertPanel(!showAlertPanel)}
            style={{
              padding: '8px 16px',
              backgroundColor: activeAlerts.length > 0 ? '#f44336' : '#ff9800',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              position: 'relative'
            }}
            title="Alert Configuration"
          >
            🔔 Alerts {activeAlerts.length > 0 && `(${activeAlerts.length})`}
          </button>

          {/* Auto-Refresh Control */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#666' }}>
              Auto-Refresh
            </label>
            <select
              value={autoRefreshInterval}
              onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
              style={{
                padding: '8px 12px',
                borderRadius: 4,
                border: '1px solid #ddd',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              <option value={0}>Off</option>
              <option value={5000}>5 seconds</option>
              <option value={15000}>15 seconds</option>
              <option value={30000}>30 seconds</option>
              <option value={60000}>1 minute</option>
              <option value={300000}>5 minutes</option>
            </select>
          </div>

          {/* Dark Mode Toggle */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            style={{
              padding: '8px 16px',
              backgroundColor: darkMode ? '#333' : '#f5f5f5',
              color: darkMode ? 'white' : '#333',
              border: '1px solid #ddd',
              borderRadius: 4,
              cursor: 'pointer',
              fontWeight: 'bold',
              transition: 'all 0.3s ease'
            }}
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {darkMode ? '☀️ Light' : '🌙 Dark'}
          </button>

          {/* Comparison Mode Toggle */}
          <button
            onClick={() => setComparisonMode(!comparisonMode)}
            style={{
              padding: '8px 16px',
              backgroundColor: comparisonMode ? '#2196f3' : '#f5f5f5',
              color: comparisonMode ? 'white' : '#333',
              border: comparisonMode ? '1px solid #2196f3' : '1px solid #ddd',
              borderRadius: 4,
              cursor: 'pointer',
              fontWeight: comparisonMode ? 'bold' : 'normal',
            }}
            title="Compare two time periods"
          >
            📊 Compare
          </button>
        </div>
      </div>

      {/* Comparison Mode Date Selectors */}
      {comparisonMode && (
        <div style={{
          marginTop: 16,
          marginBottom: 16,
          padding: 16,
          backgroundColor: '#e3f2fd',
          borderRadius: 8,
          border: '1px solid #2196f3',
        }}>
          <h4 style={{ marginTop: 0, marginBottom: 12, color: '#1976d2' }}>
            📊 Comparison Period
          </h4>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#666' }}>
                Comparison Start
              </label>
              <input
                type="datetime-local"
                value={comparisonDateRange.start}
                onChange={(e) => setComparisonDateRange({ ...comparisonDateRange, start: e.target.value })}
                style={{
                  padding: '8px 12px',
                  borderRadius: 4,
                  border: '1px solid #2196f3',
                  fontSize: '14px'
                }}
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#666' }}>
                Comparison End
              </label>
              <input
                type="datetime-local"
                value={comparisonDateRange.end}
                onChange={(e) => setComparisonDateRange({ ...comparisonDateRange, end: e.target.value })}
                style={{
                  padding: '8px 12px',
                  borderRadius: 4,
                  border: '1px solid #2196f3',
                  fontSize: '14px'
                }}
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#666' }}>
                Quick Set
              </label>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={() => {
                    const now = new Date();
                    const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);
                    setComparisonDateRange({
                      start: formatDateForInput(twoWeeksAgo),
                      end: formatDateForInput(oneWeekAgo)
                    });
                  }}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: 'white',
                    border: '1px solid #2196f3',
                    borderRadius: 4,
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Previous Week
                </button>
                <button
                  onClick={() => {
                    const now = new Date();
                    const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                    const twoMonthsAgo = new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000);
                    setComparisonDateRange({
                      start: formatDateForInput(twoMonthsAgo),
                      end: formatDateForInput(oneMonthAgo)
                    });
                  }}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: 'white',
                    border: '1px solid #2196f3',
                    borderRadius: 4,
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Previous Month
                </button>
              </div>
            </div>
            <div style={{ fontSize: '12px', color: '#1976d2', fontStyle: 'italic', marginTop: 'auto' }}>
              ℹ️ Current period vs comparison period will be shown side-by-side
            </div>
          </div>
        </div>
      )}

      {/* View Mode Toggle */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: 12,
        gap: 8,
        alignItems: 'center'
      }}>
        <button
          onClick={() => setShowStats(!showStats)}
          style={{
            padding: '8px 16px',
            backgroundColor: showStats ? '#4caf50' : '#f5f5f5',
            color: showStats ? 'white' : '#333',
            border: showStats ? '1px solid #4caf50' : '1px solid #ddd',
            borderRadius: 4,
            cursor: 'pointer',
            fontWeight: showStats ? 'bold' : 'normal',
          }}
        >
          📈 {showStats ? 'Hide' : 'Show'} Statistics
        </button>

        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setViewMode('chart')}
            style={{
              padding: '8px 16px',
              backgroundColor: viewMode === 'chart' ? '#8884d8' : '#f5f5f5',
              color: viewMode === 'chart' ? 'white' : '#333',
              border: viewMode === 'chart' ? '1px solid #8884d8' : '1px solid #ddd',
              borderRadius: 4,
              cursor: 'pointer',
              fontWeight: viewMode === 'chart' ? 'bold' : 'normal',
            }}
          >
            📊 Chart View
          </button>
          <button
            onClick={() => setViewMode('table')}
            style={{
              padding: '8px 16px',
              backgroundColor: viewMode === 'table' ? '#8884d8' : '#f5f5f5',
              color: viewMode === 'table' ? 'white' : '#333',
              border: viewMode === 'table' ? '1px solid #8884d8' : '1px solid #ddd',
              borderRadius: 4,
              cursor: 'pointer',
              fontWeight: viewMode === 'table' ? 'bold' : 'normal',
            }}
          >
            📋 Table View
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: 2, marginBottom: 24, borderBottom: '1px solid #ddd' }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '12px 20px',
              border: 'none',
              background: activeTab === tab.id ? '#8884d8' : '#f5f5f5',
              color: activeTab === tab.id ? 'white' : '#333',
              cursor: 'pointer',
              borderRadius: '8px 8px 0 0',
              fontSize: '14px',
              fontWeight: activeTab === tab.id ? 'bold' : 'normal',
            }}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Statistical Summaries */}
      {showStats && (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ marginBottom: 16 }}>Statistical Summary</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
            {activeTab === 'overview' && (
              <>
                <StatisticalSummary title="CPU Utilization (%)" data={perf.data} field="data.cpu.utilization_percent" />
                <StatisticalSummary title="Memory Usage (%)" data={perf.data} field="data.memory.ram_percent" />
                <StatisticalSummary title="Network RX (MB)" data={perfData} field="network_rx" />
              </>
            )}
            {activeTab === 'engagement' && (
              <>
                <StatisticalSummary title="Session Duration (min)" data={engagementSessions.data} field="data.duration_minutes" />
                <StatisticalSummary title="Commands per Session" data={engagementSessions.data} field="data.commands_count" />
              </>
            )}
            {activeTab === 'learning' && (
              <>
                <StatisticalSummary title="Progress (%)" data={learningProgress.data} field="data.progress_percent" />
                <StatisticalSummary title="Score" data={learningProgress.data} field="data.score" />
              </>
            )}
            {activeTab === 'usage' && (
              <>
                <StatisticalSummary title="App Duration (min)" data={appUsageStats.data} field="data.duration_minutes" />
              </>
            )}
            {activeTab === 'risk' && (
              <>
                <StatisticalSummary title="Risk Score" data={dropoutRiskAssessment.data} field="data.risk_score" />
              </>
            )}
          </div>
        </div>
      )}

      {/* Tab Content */}
      <div data-tab-content style={{ marginTop: 16 }}>
      {viewMode === 'chart' ? (
        renderTabContent()
      ) : (
        // Table View
        <div>
          {activeTab === 'overview' && <DataTable data={perfData} />}
          {activeTab === 'engagement' && <DataTable data={engagementData} />}
          {activeTab === 'learning' && <DataTable data={learningProgress.data} />}
          {activeTab === 'usage' && <DataTable data={appUsageStats.data} />}
          {activeTab === 'risk' && <DataTable data={dropoutRiskAssessment.data} />}
          {activeTab === 'comparison' && <DataTable data={crossServerMetrics.data} />}
          {activeTab === 'security' && <DataTable data={commands.data} />}
          {activeTab === 'analytics' && <DataTable data={dailyActivity.data} />}
          {activeTab === 'developer' && (
            <div>
              <h4>FileSystem Activity</h4>
              <DataTable data={filesystemData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Error/Debug Data</h4>
              <DataTable data={errorDebugData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Dev Environment</h4>
              <DataTable data={devEnvironmentData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Browser Activity</h4>
              <DataTable data={browserActivityData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Code Quality</h4>
              <DataTable data={codeQualityData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Package Dependencies</h4>
              <DataTable data={packageDependencyData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Collaboration</h4>
              <DataTable data={collaborationData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Learning Path</h4>
              <DataTable data={learningPathData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Resource Access</h4>
              <DataTable data={resourceAccessData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Time Distribution</h4>
              <DataTable data={timeDistributionData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Hardware Utilization</h4>
              <DataTable data={hardwareUtilizationData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Network Behavior</h4>
              <DataTable data={networkBehaviorData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Terminal/Console</h4>
              <DataTable data={terminalConsoleData.data} maxRows={50} />
              <h4 style={{ marginTop: 24 }}>Project Lifecycle</h4>
              <DataTable data={projectLifecycleData.data} maxRows={50} />
            </div>
          )}
        </div>
      )}
      </div>

      {/* Debug Info */}
      <div style={{ marginTop: 24, padding: 16, backgroundColor: '#f9f9f9', borderRadius: 8, fontSize: '12px' }}>
        <h4>Debug Info</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <div>📊 Performance: {perf.data.length} records</div>
          <div>🎯 Engagement: {engagementSessions.data.length} sessions</div>
          <div>🧠 Learning: {learningProgress.data.length} progress records</div>
          <div>📱 Apps: {appUsageStats.data.length} usage records</div>
          <div>📅 Daily: {dailyActivity.data.length} activity records</div>
          <div>⚠️ Risk: {dropoutRiskAssessment.data.length} assessments</div>
          <div>🔄 Cross-Server: {crossServerMetrics.data.length} comparisons</div>
        </div>
      </div>
      </div> {/* End Main Content wrapper */}
    </div>
  );
}
