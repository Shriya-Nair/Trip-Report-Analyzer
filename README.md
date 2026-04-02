# Trip-Report-Analyzer
Monthly Trip Report Analyzer - A Streamlit web application that processes logistics trip reports to analyze client-wise trips, destination patterns, plant-wise distribution, and trip type breakdowns (Loaded/Empty). Upload Excel files to get interactive dashboards, KPIs, and downloadable summaries.

## ✨ Features

### Core Functionality
- 📁 **Multi-file Upload** - Process multiple monthly trip reports simultaneously (.xlsx format)
- 🔍 **Smart Column Detection** - Automatically identifies Source/Plant columns (Source, Source Place, Plant, Origin, From)
- 🎯 **Interactive Filtering** - Filter by Client, Plant/Source, Month, and Trip Type with real-time updates
- 📊 **Dynamic KPIs** - View total trips, unique destinations, plants covered, and monthly trends at a glance

### Analytics & Visualization
- 📍 **Destination Analysis** - Trip distribution by destination with bar charts and data tables
- 🏭 **Plant Breakdown** - Plant-wise trip distribution and utilization metrics
- 📈 **Monthly Trends** - Track trip volumes over time with line charts
- 🔄 **Trip Type Analysis** - Loaded vs Empty trip breakdown (when data available)
- 🎨 **Interactive Charts** - All visualizations update dynamically with filters

### Export & Reporting
- 📎 **Excel Export** - Download filtered summaries as Excel files with multiple sheets:
  - Destination Summary sheet
  - Raw Trips data sheet
  - Plant Summary sheet (when applicable)
