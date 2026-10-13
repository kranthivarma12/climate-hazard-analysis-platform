# Climate Hazard Analysis Platform — Historical Heatwave Analysis

A full-stack, scientifically grounded web platform for detecting historical heatwave events, modeling regional temperature thresholds, and quantifying decadal climate hazard trends from empirical weather data.

---

## 1. Project Overview & Features

The **Climate Hazard Analysis Platform** enables environmental scientists, urban planners, and climate analysts to assess historical heatwave exposure across any geographic location worldwide between 1950 and 2024.

### Core Capabilities
- **Empirical Heatwave Detection:** Identifies distinct episodes where daily maximum 2-meter air temperature ($T_{\text{max}}$) strictly exceeds the regional 95th-percentile baseline threshold for $\ge 3$ consecutive calendar days.
- **WMO-Standard Climatological Baselines:** Computes regional percentiles from a configurable 30-year normal reference period (default: 1991–2020), isolated from the analysis timeframe.
- **Continuous Boundary Handling:** Correctly detects heatwaves that span calendar-year boundaries (e.g., Dec 30 – Jan 2) and attributes heatwave days to their respective calendar years without double-counting.
- **Statistical Trend Rigor:** Fits Ordinary Least Squares (OLS) regressions using SciPy to compute decadal slopes (events/decade, days/decade), Pearson $R^2$, and $p$-value statistical significance.
- **Zero-Division Safeguards:** Protects period comparisons against division by zero when the early baseline period contains zero events.
- **MongoDB Observation & Result Caching:** Persists raw daily weather observations and complete parameterized analysis records, preventing redundant third-party API calls.
- **Scientific Visualization Dashboard:** Interactive Chart.js charts for annual episode frequency, cumulative heatwave days, and peak intensity curves.
- **Comprehensive Data Quality Auditing:** Reports completeness percentage, missing observations count, and screened anomalous readings.
- **Dual CSV Export:** One-click CSV export of annual aggregate time-series and granular event logs.

---

## 2. Architecture & Data Flow

```
[ React SPA + Tailwind CSS + Chart.js ]
                  │
                  ▼ (Port 3000)
    [ Express Reverse Gateway / Vite Dev Server ]
                  │
                  ▼ (Proxy /api/* to Port 8001)
     [ FastAPI Python Application Layer ]
      ├── Pydantic Input/Output Schemas
      ├── Open-Meteo Ingestion & Quality Control
      ├── Heatwave Detection Algorithm (95th Pctile)
      ├── SciPy Linear Regression Trend Analysis
      └── MongoDB Repository Layer
            ├── weather_daily collection (Unique index: lat+lon+date)
            └── analysis_results collection (Unique index: params hash)
                  │
                  ▼
         [ MongoDB 7.0 Engine ]
```

### Request Flow
1. User selects a preset region or inputs latitude/longitude and historical years.
2. The React frontend sends an HTTP request to `GET /api/v1/analysis`.
3. The FastAPI router queries MongoDB's `analysis_results` cache using the exact parameter tuple `(lat, lon, start_year, end_year, baseline_start, baseline_end, hazard, version)`.
4. **On Cache Hit:** The document is returned immediately with `cache_status: "HIT"`.
5. **On Cache Miss:**
   - The weather service checks `weather_daily` in MongoDB. Any missing days are ingested from Open-Meteo's ERA5 archive.
   - Temperature anomalies outside physical bounds ($[-90^\circ\text{C}, 65^\circ\text{C}]$) are rejected.
   - Missing calendar days are explicitly represented (never replaced with zeros).
   - The 95th percentile baseline threshold is derived over the baseline period.
   - Heatwave episodes ($\ge 3$ consecutive days) are identified over the continuous daily index.
   - Annual aggregates and SciPy decadal trend slopes are calculated.
   - The final result is cached in MongoDB and returned to the frontend.

---

## 3. Technology Stack

- **Frontend:** React 19, Vite, TypeScript, Tailwind CSS, Lucide React.
- **Charts:** Chart.js 4, react-chartjs-2.
- **Backend:** Python 3.11, FastAPI, Uvicorn, Pydantic v2.
- **Scientific Computing:** Pandas, NumPy, SciPy (scipy.stats.linregress).
- **External Data Source:** Open-Meteo Historical Weather API (ERA5 Reanalysis).
- **Database:** MongoDB 7.0 (PyMongo).
- **Testing:** Pytest & pytest-asyncio for Python.
- **Containerization:** Docker & Docker Compose.

---

## 4. Prerequisites

- **Node.js:** v18+ or v22+
- **Python:** 3.10+ or 3.11+
- **MongoDB:** MongoDB Community Server 6.0+ or 7.0+ (or run via Docker Compose)

---

## 5. Local Setup Instructions

### Option A: Running with Docker Compose (Recommended)

```bash
# 1. Clone repository
git clone <repo-url>
cd climate-hazard-platform

# 2. Build and launch all three services (MongoDB, FastAPI, React frontend)
docker compose up --build
```
Access the application at `http://localhost:3000`.

---

### Option B: Native Manual Setup

#### 1. MongoDB Setup
**Linux / macOS:**
```bash
# Start MongoDB daemon
mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db --bind_ip 127.0.0.1
```
**Windows PowerShell:**
```powershell
# Start MongoDB service (if installed via MSI)
net start MongoDB
# Or run mongod directly:
mongod --dbpath "C:\data\db"
```

#### 2. Backend Setup
**Linux / macOS:**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend on port 8001
uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
```

**Windows PowerShell:**
```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend on port 8001
uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
```

#### 3. Frontend Setup
**In a separate terminal:**
```bash
# Install node dependencies
npm install

# Start development server on port 3000
npm run dev
```

The React frontend starts at `http://localhost:3000` and automatically proxies `/api/*` to the FastAPI backend at `http://localhost:8001`.

---

## 6. Environment Variables

Create `.env` using `.env.example` as a template:

```env
# MongoDB Connection String
MONGODB_URI="mongodb://127.0.0.1:27017/climate_hazard"

# Backend Binding
BACKEND_HOST="0.0.0.0"
BACKEND_PORT=8001

# Frontend Proxy Target & API Base URL
PORT=3000
VITE_API_BASE_URL="/api/v1"
```

---

## 7. API Endpoints

### `GET /api/v1/health`
Checks backend and MongoDB database connectivity.
```json
{
  "status": "healthy",
  "database_connected": true,
  "database_uri_configured": "mongodb://127.0.0.1:27017/climate_hazard",
  "version": "1.0.0",
  "timestamp": "2026-10-12T04:25:22.146296+00:00"
}
```

### `GET /api/v1/regions`
Returns supported global climate preset cities.

### `GET /api/v1/analysis`
Performs historical heatwave analysis.
- **Parameters:**
  - `latitude` (float, required): -90.0 to 90.0
  - `longitude` (float, required): -180.0 to 180.0
  - `start_year` (int, default: 1990)
  - `end_year` (int, default: 2020)
  - `hazard` (str, default: "heatwave")
  - `baseline_start` (int, default: 1991)
  - `baseline_end` (int, default: 2020)
  - `force_refresh` (bool, default: false)

### `GET /api/v1/events`
Returns list of detected episodes with optional `min_duration` filter.

### `POST /api/v1/cache/refresh`
Evicts cache entries for the given parameters and triggers fresh retrieval.

---

## 8. Automated Testing

The test suite covers algorithmic edge cases, data sanitization, linear regressions, and API routes with zero external dependencies.

```bash
# Run backend pytest suite
PYTHONPATH=. /app/venv/bin/pytest backend/tests/ -v

# Or via npm script
npm run test:backend
```

### Test Coverage Breakdown:
1. `test_threshold_known_synthetic_dataset`: Derivation against synthetic distribution.
2. `test_insufficient_baseline_data_raises_error`: Clean failure when baseline completeness is $< 80\%$.
3. `test_duplicate_dates_and_missing_values_cleaned`: Deduplication and NaN preservation.
4. `test_exactly_two_hot_days_no_heatwave`: Verifies strict $\ge 3$ consecutive days rule.
5. `test_exactly_three_consecutive_hot_days_one_heatwave`: Exactly one qualifying episode.
6. `test_four_or_more_consecutive_hot_days_one_event`: Multi-day single episode containment.
7. `test_below_threshold_day_breaks_episode`: Sub-threshold day episode termination.
8. `test_missing_calendar_day_breaks_episode`: Missing date break behavior.
9. `test_events_spanning_calendar_year_boundary`: Continuous episode detection across year transition and double-counting prevention.
10. `test_regression_increasing_direction_and_units`: OLS slope calculation and decadal scaling ($10\times$).
11. `test_regression_decreasing_direction`: Downward slope verification.
12. `test_regression_stable_zero_slope`: Flat trend verification.
13. `test_undefined_percent_change_when_baseline_is_zero`: Guards against division by zero.
14. `test_weather_service_screening`: Rejection of temperatures outside $[-90^\circ\text{C}, 65^\circ\text{C}]$.
15. `test_api_endpoints`: Integration verification with mock HTTP clients.

---

## 9. Database Schema & Caching Strategy

### Collection: `weather_daily`
Stores ingested daily observations:
- `latitude` (float, rounded to 4 decimals)
- `longitude` (float, rounded to 4 decimals)
- `date` (string YYYY-MM-DD)
- `temperature_2m_max` (float in Celsius)
- `source` ("open-meteo-archive")
- `retrieved_at` (ISO timestamp)
- **Unique Index:** `("latitude", "longitude", "date")`

### Collection: `analysis_results`
Stores complete computed analytical results:
- Unique Compound Index:
  - `("latitude", "longitude", "start_year", "end_year", "baseline_start", "baseline_end", "hazard", "algorithm_version")`

---

## 10. Security & Performance

- **No Secret Leakage:** No API keys are embedded or committed; `.env.example` contains only non-secret configuration variables.
- **Input Validation:** Strict Pydantic boundary validation for coordinates $[-90, 90]$ and $[-180, 180]$, preventing arbitrary injection.
- **SSRF Prevention:** The backend queries only the fixed, predefined Open-Meteo archive endpoint; user-supplied URLs cannot be ingested.
- **Database Indexes:** Compound unique indexes enforce data integrity and sub-millisecond cache lookups.
- **Bounded HTTP Requests:** Ingestion requests enforce a 30-second timeout.

---

## 11. Known Limitations & Future Roadmap

1. **Seasonal Percentiles:** Currently uses an annual regional 95th percentile. Day-of-year seasonal moving window percentiles (e.g. 15-day window) will be added to provide seasonal heatwave nuances in temperate zones.
2. **Additional Hazards:** Drought (SPI / SPEI) and extreme rainfall (R95p) algorithms will be added in subsequent milestones.
3. **Mann-Kendall Trend Testing:** Supplementing linear OLS regression with the non-parametric Mann-Kendall test.

---

## 12. Honest Disclosure of AI Tools Used

This application was engineered by senior software engineer and data engineer AI agents using Claude / Gemini coding capabilities. The AI tools were utilized for:
- Implementing the mathematical baseline thresholding and episode detection algorithm according to WMO specifications.
- Structuring the FastAPI routers, Pydantic schemas, and PyMongo caching layer.
- Developing the React dashboard with Chart.js visualizations following scientific design standards.
- Authoring exhaustive unit and integration tests covering deterministic boundary and error states.
