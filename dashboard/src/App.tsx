// Version: 2025-01-15-v3 - Fixed chart line hiding with conditional rendering
import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { LineChart, BarChart, PieChart, AreaChart, ComposedChart, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid, Cell, Line, Bar, Area, Pie } from 'recharts';

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

  // Data fetching with new comprehensive data sources
  const perf = useESWithDateFilter<PerfDoc>(baseUrl, index, 'event_type:performance_metrics', startDate, endDate, availableIndices);
  const cmds = useESWithDateFilter<CommandDoc>(
    baseUrl,
    index,
    'event_type:monitoring_summary',
    startDate,
    endDate,
    availableIndices
  );
  const windows = useESWithDateFilter<WindowUsageDoc>(baseUrl, index, 'event_type:user_activity', startDate, endDate, availableIndices);
  
  // New engagement data sources
  const engagementSessions = useESWithDateFilter<EngagementSessionDoc>(baseUrl, index, 'event_type:engagement_session', startDate, endDate, availableIndices);
  // Pull command activity from both direct command events and monitoring summaries
  const commandEngagement = useESWithDateFilter<CommandDoc>(
    baseUrl,
    index,
    'event_type:monitoring_summary',
    startDate,
    endDate,
    availableIndices
  );
  const learningProgress = useESWithDateFilter<LearningProgressDoc>(baseUrl, index, 'event_type:learning_progress', startDate, endDate, availableIndices);
  const appUsageStats = useESWithDateFilter<AppUsageDoc>(baseUrl, index, 'event_type:app_usage_stats', startDate, endDate, availableIndices);
  const dailyActivity = useESWithDateFilter<DailyActivityDoc>(baseUrl, index, 'event_type:daily_activity', startDate, endDate, availableIndices);
  const engagementMetrics = useESWithDateFilter<EngagementSessionDoc>(baseUrl, index, 'event_type:engagement_metrics', startDate, endDate, availableIndices);
  const skillProgressAnalytics = useESWithDateFilter<LearningProgressDoc>(baseUrl, index, 'event_type:skill_progress_analytics', startDate, endDate, availableIndices);
  const skillCrossComparison = useESWithDateFilter<LearningProgressDoc>(baseUrl, index, 'event_type:skill_cross_comparison', startDate, endDate, availableIndices);
  const dropoutRiskAssessment = useESWithDateFilter<DropoutRiskDoc>(baseUrl, index, 'event_type:dropout_risk_assessment', startDate, endDate, availableIndices);
  const crossServerMetrics = useESWithDateFilter<CrossServerDoc>(baseUrl, index, 'event_type:cross_server_metrics', startDate, endDate, availableIndices);
  const crossServerComparison = useESWithDateFilter<CrossServerDoc>(baseUrl, index, 'event_type:cross_server_comparison', startDate, endDate, availableIndices);

  const isLoading = useMemo(() => 
    perf.isLoading || cmds.isLoading || windows.isLoading || 
    engagementSessions.isLoading || commandEngagement.isLoading || learningProgress.isLoading || 
    appUsageStats.isLoading || dailyActivity.isLoading || engagementMetrics.isLoading || 
    skillProgressAnalytics.isLoading || skillCrossComparison.isLoading || dropoutRiskAssessment.isLoading || 
    crossServerMetrics.isLoading || crossServerComparison.isLoading,
    [perf.isLoading, cmds.isLoading, windows.isLoading, 
     engagementSessions.isLoading, commandEngagement.isLoading, learningProgress.isLoading, 
     appUsageStats.isLoading, dailyActivity.isLoading, engagementMetrics.isLoading, 
     skillProgressAnalytics.isLoading, skillCrossComparison.isLoading, dropoutRiskAssessment.isLoading, 
     crossServerMetrics.isLoading, crossServerComparison.isLoading]
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

  // No Data component
  const NoDataMessage = ({ message = "No data available for the selected time range" }: { message?: string }) => (
    <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
      <div className="text-center">
        <div className="text-gray-400 text-6xl mb-4">📊</div>
        <p className="text-gray-500 text-lg">{message}</p>
        <p className="text-gray-400 text-sm mt-2">Try selecting a different time range</p>
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
    { id: 'analytics', label: 'Advanced Analytics', icon: '📈' }
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
          <ResponsiveContainer width="100%" height={290}>
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
                height={120}
                tick={{ fontSize: 9 }}
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
          <ResponsiveContainer width="100%" height={300}>
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
                <Line type="monotone" dataKey="cpu" stroke="#8884d8" name="CPU %" strokeWidth={2} connectNulls={true} />
              )}
        </LineChart>
      </ResponsiveContainer>
          )}

          <h3>Memory Usage</h3>
          {perfData.length === 0 ? (
            <NoDataMessage message="No Memory data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={300}>
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
                <Line type="monotone" dataKey="memory" stroke="#82ca9d" name="Memory %" strokeWidth={2} connectNulls={true} />
              )}
            </LineChart>
          </ResponsiveContainer>
          )}

          <h3>Disk Usage</h3>
          {perfData.length === 0 ? (
            <NoDataMessage message="No Disk data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={300}>
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
                <Line type="monotone" dataKey="disk" stroke="#ffc658" name="Disk GB" strokeWidth={2} connectNulls={true} />
              )}
            </LineChart>
          </ResponsiveContainer>
          )}

          <h3>Network RX (Receive)</h3>
          {perfData.length === 0 ? (
            <NoDataMessage message="No network RX data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={perfData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="dateTime"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={100}
                tickFormatter={(value, index) => {
                  // Only show every 3rd tick to reduce clutter
                  if (index % 3 !== 0) {
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
                <Line type="monotone" dataKey="network_rx" stroke="#8884d8" name="RX MB" strokeWidth={2} connectNulls={true} />
              )}
            </LineChart>
          </ResponsiveContainer>
          )}

          <h3>Network TX (Transmit)</h3>
          {perfData.length === 0 ? (
            <NoDataMessage message="No network TX data available for the selected time range." />
          ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={perfData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="dateTime"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={100}
                tickFormatter={(value, index) => {
                  // Only show every 3rd tick to reduce clutter
                  if (index % 3 !== 0) {
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
                <Line type="monotone" dataKey="network_tx" stroke="#82ca9d" name="TX MB" strokeWidth={2} connectNulls={true} />
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
      
      default: return (
        <div>
          <h3>Overview</h3>
          <NoDataMessage message="No performance data available for the selected time range" />
        </div>
      );
    }
  };

  return (
    <div ref={dashboardRef} style={{ fontFamily: 'sans-serif', padding: 16 }}>
      {/* Loading Overlay */}
      {(isLoading || isGeneratingPDF) && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            fontSize: '18px',
            fontWeight: 'bold',
            color: '#333',
          }}
        >
          {isGeneratingPDF ? 'Generating PDF...' : 'Loading...'}
        </div>
      )}

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

      {/* Tab Content */}
      <div data-tab-content style={{ marginTop: 16 }}>
      {renderTabContent()}
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
    </div>
  );
}
