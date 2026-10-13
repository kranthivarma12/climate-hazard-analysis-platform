# Climate Hazard Analysis Platform — Scientific Methodology Documentation

## 1. Overview and Scientific Context

Heatwaves represent one of the most direct and dangerous physical manifestations of climate variability and long-term anthropogenically forced climate change. Characterizing historical changes in heatwave frequency, cumulative exposure (heatwave days), and peak intensity requires a mathematically transparent, reproducible, and standardized analytical workflow.

This platform adheres to WMO (World Meteorological Organization) and ETCCDI (Expert Team on Climate Change Detection and Indices) foundational standards while documenting every computational rule, threshold assumption, and missing-data decision.

---

## 2. Baseline Period and Percentile Threshold Formulation

### 2.1 Reference Climatology Period
- **Default Reference Period:** 1991–2020 (WMO standard 30-year climatological normal period).
- **Configurability:** Fully configurable (e.g., 1961–1990 for pre-acceleration benchmarks or 1981–2010).
- **Separation of Baseline and Analysis:** The baseline period is treated as a reference distribution. It is independent of the user's selected analytical period, ensuring consistent, stationary threshold evaluation across comparisons.

### 2.2 95th-Percentile Threshold ($T_{95}$)
For a given geographic coordinate $(\phi, \lambda)$, all valid daily maximum 2-meter air temperatures $T_{\text{max}}(t)$ within the baseline calendar bounds are extracted:

$$S_{\text{baseline}} = \{ T_{\text{max}}(t) \mid \text{Year}(t) \in [Y_{\text{base,start}}, Y_{\text{base,end}}], \, T_{\text{max}}(t) \text{ is valid} \}$$

The regional threshold $\Theta_{95}$ is defined as the empirical 95th percentile:

$$\Theta_{95} = P_{95}(S_{\text{baseline}})$$

Computed using linear interpolation between adjacent ranks (consistent with NumPy `np.percentile(values, 95.0, method='linear')`).

### 2.3 Completeness Requirement
To prevent distorted thresholds resulting from observational gaps:
- The baseline period requires at least **80% observational completeness** of total calendar days.
- If fewer than $0.80 \times N_{\text{expected}}$ valid observations exist, the algorithm raises an explicit validation exception (`Insufficient baseline observations`) rather than deriving an unreliable threshold.

---

## 3. Heatwave Episode Detection Algorithm

### 3.1 Heatwave Definition
A heatwave episode $E_k$ is defined as a contiguous sequence of at least three calendar days where the daily maximum temperature strictly exceeds the baseline threshold:

$$T_{\text{max}}(t) > \Theta_{95} \quad \text{for all } t \in [t_{\text{start}}, t_{\text{end}}] \quad \text{with } D = (t_{\text{end}} - t_{\text{start}} + 1) \ge 3 \text{ days}$$

### 3.2 Episode Termination and Break Logic
- **Sub-threshold Days:** Any day with $T_{\text{max}}(t) \le \Theta_{95}$ immediately terminates the current episode candidate.
- **Missing Observations:** A calendar day with missing temperature data ($T_{\text{max}}(t) = \text{NaN}$) or an unobserved calendar date strictly terminates the run. Missing observations are never filled with zero or imputed with unverified synthetic values.

### 3.3 Event-Level Metrics
For each detected episode $E_k = \{ (t_i, T_i) \}_{i=1}^D$:
1. **Start Date:** $t_{\text{start}} = t_1$ (ISO 8601 YYYY-MM-DD).
2. **End Date:** $t_{\text{end}} = t_D$ (ISO 8601 YYYY-MM-DD).
3. **Duration:** $D = t_D - t_1 + 1$ (calendar days).
4. **Peak Daily Maximum Temperature:** $T_{\text{peak}} = \max_{i=1}^D T_i$ (°C).
5. **Mean Episode Temperature:** $\bar{T} = \frac{1}{D} \sum_{i=1}^D T_i$ (°C).
6. **Mean Exceedance:** $\Delta \bar{T} = \frac{1}{D} \sum_{i=1}^D (T_i - \Theta_{95})$ (°C).

---

## 4. Annual Aggregations and Boundary Allocation

### 4.1 Boundary Spanning Events
When an episode crosses a calendar-year boundary (e.g., starting December 30 in Year $Y$ and ending January 2 in Year $Y+1$):
- **Episode Count Attribution:** The episode is attributed to its **start year** for the annual episode count metric.
- **Heatwave Days Attribution:** The actual calendar days are attributed to their **respective calendar years**. For the Dec 30–Jan 2 event:
  - Year $Y$ receives 2 heatwave days (Dec 30, Dec 31).
  - Year $Y+1$ receives 2 heatwave days (Jan 1, Jan 2).
- **Double Counting Prevention:** This guarantees that the sum of heatwave days across all years equals the exact sum of episode durations across the dataset.

### 4.2 Annual Summary Metrics
For each calendar year $Y$:
- **Event Count ($N_{\text{events}}$):** Count of heatwave episodes initiated in year $Y$.
- **Heatwave Days ($N_{\text{days}}$):** Total calendar days in year $Y$ belonging to any detected heatwave episode.
- **Mean Duration:** $\frac{1}{N_{\text{events}}} \sum D_k$ for events initiated in year $Y$ (null if $N_{\text{events}} = 0$).
- **Peak Intensity:** $\max(T_i)$ for all heatwave days in year $Y$ (null if $N_{\text{days}} = 0$).
- **Mean Intensity:** $\frac{1}{N_{\text{days}}} \sum T_i$ for all heatwave days in year $Y$.
- **Valid Observations & Missing Days:** Tracked explicitly for data quality assurance.

---

## 5. Trend Estimation and Statistical Rigor

### 5.1 Linear Regression
Trends across annual time series are computed using Ordinary Least Squares (OLS) regression via `scipy.stats.linregress`:

$$\hat{y}_t = \beta_1 \cdot t + \beta_0$$

Where:
- $\beta_1$ represents the annual rate of change (slope per year).
- **Decadal Trend:** $\beta_{\text{decade}} = \beta_1 \times 10$ (events/decade or days/decade).
- **Coefficient of Determination ($R^2$):** Square of Pearson correlation coefficient.
- **Statistical Significance ($p$-value):** Two-sided hypothesis test against the null hypothesis $\beta_1 = 0$. $p < 0.05$ denotes statistical significance at the 95% confidence level.

### 5.2 Period Comparison & Zero-Baseline Guard
The earliest window (e.g., first 10 years) and latest window (e.g., last 10 years) are compared:
- Let $\bar{y}_{\text{early}}$ and $\bar{y}_{\text{late}}$ denote the respective period means.
- **Percentage Change:**

$$\Delta \% = \frac{\bar{y}_{\text{late}} - \bar{y}_{\text{early}}}{\bar{y}_{\text{early}}} \times 100\%$$

- **Zero-Baseline Safeguard:** If $\bar{y}_{\text{early}} = 0$, division by zero is strictly disallowed. The percentage change is set to `null` and reported in the interface as `"Undefined (+X.X events/yr from zero baseline)"`.

---

## 6. Known Assumptions and Methodological Limitations

1. **Fixed Regional vs. Seasonal Day-of-Year Threshold:** The current implementation uses an annual regional 95th-percentile threshold. In high-latitude or continental climates with steep seasonal temperature cycles, heatwaves naturally concentrate in summer months. A day-of-year seasonal moving window (e.g., 15-day or 31-day centered window percentile) is a scientifically sound future extension.
2. **Linear Trend Limitations:** Linear regression summarizes historical average rate of change. It does not imply that heatwave frequency scales strictly linearly into future decades.
3. **Reanalysis Grid Resolution:** Weather data is retrieved from Open-Meteo's ERA5 reanalysis archive (~0.25° grid, ~28 km). Microclimate urban heat islands may differ slightly from grid averages.
