# Enhanced Monitor Dashboard

A comprehensive React-based dashboard for visualizing lab server monitoring data from Elasticsearch.

## 🚀 Features

### **Overview Tab** 📊
- **Performance Metrics**: CPU, Memory, Disk, and Network usage over time
- **Command Durations**: Bar chart showing command execution times
- **Top Windows**: Pie chart of most-used applications/windows
- **User Analysis**: Area chart of user engagement scores

### **Engagement Tab** 🎯
- **Engagement Sessions**: Combined line/bar/scatter chart showing session data
- **Productive vs Break Time**: Pie chart comparing productive and break time
- **Apps Used per Session**: Bar chart of applications used in sessions

### **Skills & Learning Tab** 🧠
- **Skill Development Progress**: Bar chart of average skill levels by category
- **Learning Analytics**: Scatter plot of current level vs progress percentage

### **Performance Tab** ⚡
- **System Performance Metrics**: Line chart of system resources
- **Application Usage Analytics**: Bar chart of app usage and productivity scores

### **Analytics Tab** 📈
- **Daily Activity Patterns**: Combined chart showing daily trends
- **Dropout Risk Assessment**: Scatter plot of risk scores vs dropout probability

### **Cross-Server Tab** 🔄
- **Cross-Server Performance**: Bar chart comparing server performance
- **Server Rankings**: Performance ranking visualization

## 🛠️ Technology Stack

- **Frontend**: React 18 + TypeScript
- **Charts**: Recharts (Line, Bar, Pie, Area, Scatter, Composed charts)
- **HTTP Client**: Axios
- **Build Tool**: Vite
- **Styling**: CSS-in-JS with responsive design

## 📊 Data Sources

The dashboard connects to Elasticsearch and visualizes these data types:

### **Core Monitoring Data**
- `performance_metrics` - System performance (CPU, memory, disk, network)
- `user_activity` - User activity summaries
- `command_monitoring` - Command execution monitoring

### **Engagement & Learning Data**
- `engagement_session` - User session data with engagement scores
- `learning_progress` - Skill development tracking
- `skill_progress_analytics` - Detailed skill analytics
- `app_usage_stats` - Application usage statistics

### **Analytics & Risk Data**
- `daily_activity` - Daily user activity patterns
- `dropout_risk_assessment` - Risk prediction models
- `engagement_metrics` - Real-time engagement data

### **Cross-Server Data**
- `cross_server_metrics` - Server comparison metrics
- `cross_server_comparison` - Performance analysis across servers

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ 
- npm or yarn
- Access to Elasticsearch instance

### Installation
```bash
cd dashboard
npm install
```

### Development
```bash
npm run dev
```

### Build
```bash
npm run build
```

### Preview
```bash
npm run preview
```

## ⚙️ Configuration

### Elasticsearch Connection
- **URL**: Default: `https://es.zippyops.com`
- **Index**: Default: `lab_monitoring`
- **Authentication**: Configure in Elasticsearch settings

### Data Queries
The dashboard automatically queries Elasticsearch for:
- Recent data (last 200 records)
- Sorted by timestamp (newest first)
- Filtered by data type

## 📈 Chart Types

### **Line Charts**
- Performance metrics over time
- Engagement scores
- Learning progress

### **Bar Charts**
- Command durations
- Application usage
- Skill levels
- Server comparisons

### **Pie Charts**
- Window usage distribution
- Productive vs break time

### **Area Charts**
- User engagement trends
- Daily activity patterns

### **Scatter Charts**
- Learning analytics
- Risk assessment

### **Composed Charts**
- Multi-metric visualizations
- Combined line/bar/scatter data

## 🎨 Design Features

- **Responsive Layout**: Adapts to different screen sizes
- **Tab Navigation**: Organized by data category
- **Color Coding**: Consistent color scheme across charts
- **Interactive Elements**: Hover tooltips and legends
- **Grid Layout**: Efficient use of screen space

## 📱 Responsive Design

- **Desktop**: Full-width charts with side-by-side layouts
- **Tablet**: Adjusted chart heights and grid layouts
- **Mobile**: Stacked charts with optimized spacing

## 🔍 Data Processing

### **Real-time Updates**
- Automatic data refresh from Elasticsearch
- Efficient data processing with useMemo
- Optimized rendering for large datasets

### **Data Aggregation**
- Time-based grouping for trends
- Statistical calculations (averages, sums)
- Smart filtering and sorting

## 🚀 Performance Optimizations

- **Memoized Calculations**: Prevents unnecessary re-computations
- **Lazy Loading**: Charts render only when needed
- **Efficient Queries**: Optimized Elasticsearch queries
- **Responsive Containers**: Charts adapt to container size

## 🔧 Customization

### **Adding New Charts**
1. Define new data types in TypeScript
2. Add Elasticsearch queries
3. Create data processing functions
4. Implement chart rendering
5. Add to appropriate tab

### **Modifying Existing Charts**
- Update data processing logic
- Modify chart configurations
- Adjust styling and colors

## 📊 Data Visualization Best Practices

- **Consistent Scales**: Appropriate Y-axis ranges
- **Clear Labels**: Descriptive chart titles and axis labels
- **Color Consistency**: Meaningful color coding
- **Interactive Elements**: Hover tooltips and legends
- **Responsive Design**: Adapts to different screen sizes

## 🐛 Troubleshooting

### **Common Issues**
- **No Data Displayed**: Check Elasticsearch connection and index
- **Charts Not Rendering**: Verify data format and structure
- **Performance Issues**: Check data volume and query optimization

### **Debug Mode**
Enable console logging for troubleshooting:
```typescript
console.log('Data received:', data);
```

## 🔮 Future Enhancements

### **Planned Features**
- **Real-time Updates**: WebSocket integration for live data
- **Advanced Filtering**: Date ranges and user selection
- **Export Functionality**: PDF/PNG chart export
- **Custom Dashboards**: User-configurable layouts
- **Alerting**: Threshold-based notifications

### **Potential Integrations**
- **Grafana**: Advanced visualization options
- **Kibana**: Enhanced Elasticsearch analytics
- **Prometheus**: Additional metrics sources

## 📚 API Reference

### **Elasticsearch Queries**
```typescript
// Example query structure
{
  size: 200,
  sort: [{ timestamp: { order: 'desc' } }],
  query: { query_string: { query: 'type:performance' } }
}
```

### **Chart Components**
```typescript
// Line Chart
<LineChart data={data}>
  <Line dataKey="value" stroke="#8884d8" />
</LineChart>

// Bar Chart
<BarChart data={data}>
  <Bar dataKey="value" fill="#82ca9d" />
</BarChart>
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the Lab Server Monitoring AI Agent system.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section
- Review Elasticsearch logs
- Verify data format and structure
- Check network connectivity

---

**Dashboard Version**: 2.0.0  
**Last Updated**: September 2024  
**Compatible with**: Monitor Agent v2.0+
