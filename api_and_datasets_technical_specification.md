# Carbon Footprint Tracker - API Implementation & Datasets Technical Specification

> **PDF Download Available:**  
> The comprehensive PDF report has been compiled and saved outside the project codebase:  
> [📥 Download API & Datasets Technical Report (PDF)](file:///Users/sakshisanjaykumbhar/.gemini/antigravity-ide/brain/61f97616-9ef5-41c1-8f5b-89a3a4b0f751/Carbon_Tracker_API_and_Datasets_Technical_Report.pdf)

---

## 1. Interface Architecture Overview

The Carbon Tracker application uses a modular REST API architecture coupled with real-time external spatial services and a relational MySQL data layer:
- **Client Transport:** Asynchronous browser `fetch()` requests transmitting JSON payloads.
- **Session Authentication:** Stateless RFC 7519 JSON Web Tokens (JWT) verified via HTTP-only cookies and Bearer tokens.
- **Throttling & Security:** Rate limiting via Flask-Limiter, input sanitization, and SQL injection prevention via parameterized PyMySQL cursors.

---

## 2. Complete Internal REST API Catalog

### 2.1 Authentication & Profile APIs
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/register` | Public | Validates user input, hashes password via 12-round bcrypt, creates record in `users`, and initializes `leaderboard`. |
| `POST` | `/login` | Public (5/hr) | Verifies password hash, issues 24h JWT, stores in session cookie, redirects to `/dashboard`. |
| `GET` | `/logout` | Authenticated | Clears user session cookie and token. |
| `POST` | `/settings` | Authenticated | Updates citizen preferences, city, and sets monthly carbon ceiling $B_{\text{cap}}$. |

### 2.2 Commute Logging & Live Tracking APIs
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/daily_entry` | Authenticated | Computes commute emissions considering vehicle type, traffic density, engine wear, and logs entry. |
| `GET` | `/live_tracking` | Authenticated | Delivers GPS tracker UI interfacing with HTML5 Geolocation API. |
| `POST` | `/save_live_trip` | Authenticated | Ingests real-time GPS telemetry, runs anomaly checks, computes eco-scores, awards green points, and notifies user. |

### 2.3 Route Optimization & Spatial APIs
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/route_optimizer` | Authenticated | Renders multi-route comparison interface with Leaflet.js map. |
| `POST` | `/api/calculate_routes` | Authenticated | Queries TomTom Routing API (or OSRM fallback) and returns 3 alternate paths with distance, duration, fuel, and comparative $CO_2$. |
| `POST` | `/api/save_route` | Authenticated | Saves chosen optimal route to `routes` table. |

### 2.4 Vehicle Health & Calculator APIs
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/calculate_trip` | Authenticated | Computes single trip distance, fuel cost, and $CO_2$; logs to `trip_history`. |
| `GET` | `/api/trip_history` | Authenticated | Returns history of quick calculated trips. |
| `DELETE` | `/api/trip_history/<id>`| Authenticated | Deletes specific calculated trip record. |
| `POST` | `/api/smart_assess` | Authenticated | Calculates vehicle health score, degradation multiplier $\Delta$, adjusted $CO_2$, and assigns sustainability grades. |
| `GET` | `/api/smart_history` | Authenticated | Returns historical vehicle health assessments. |
| `GET` | `/api/smart_analytics` | Authenticated | Aggregates health score distributions and component wear trends. |

### 2.5 Gamification & Notification APIs
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/rewards` | Authenticated | Renders rewards dashboard, level progress, unlocked badges, and points history. |
| `GET` | `/api/notifications/list`| Authenticated | Returns user alerts inbox (streaks, badge unlocks, over-budget warnings). |
| `POST` | `/api/notifications/read/<id>` | Authenticated | Marks specific notification as read. |
| `GET` | `/api/notifications/unread_count` | Authenticated | Polling endpoint for navbar bell notification badge. |

### 2.6 Community & Diagnostics
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/leaderboard` | Public/Auth | Ranks users by lowest $CO_2$ or highest distance, filterable by city. |
| `GET` | `/health` | Public | System health diagnostic probe returning operational status. |

---

## 3. External 3rd-Party APIs Integration

1. **TomTom Routing API:**
   - **Endpoint:** `https://api.tomtom.com/routing/1/calculateRoute/{start_lat},{start_lon}:{end_lat},{end_lon}/json`
   - **Features:** Live traffic delays (`traffic=true`), polyline coordinates, fuel consumption estimations (`fuelBudgetInLiters=50`), and alternative routes (`alternatives=3`).
2. **Open Source Routing Machine (OSRM):**
   - **Endpoint:** `https://router.project-osrm.org/route/v1/driving/{src_lon},{src_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson&alternatives=true`
   - **Features:** Seamless automatic fallback if TomTom API quota is exceeded or fails.
3. **HTML5 Browser Geolocation API:**
   - Client-side real-time GPS tracking via `navigator.geolocation.watchPosition()`, computing incremental distance deltas via the Haversine equation.

---

## 4. Complete Datasets Catalog

### 4.1 File-Based CSV Datasets
- **`data/india-vehicle-emissions.csv`:** Baseline emission factors ($0.19\text{ kg/km}$ for car, $0.075\text{ kg/km}$ for bus, $0.05\text{ kg/km}$ for bike, $0.03\text{ kg/km}$ for metro, etc.).
- **`data/delhi-traffic-congestion.csv`:** Major urban corridors with congestion multipliers (Connaught Place: $1.30$, Gurgaon Expressway: $1.40$, Dwarka: $1.00$, Default: $1.10$).
- **`data/fuel_data.csv`:** Fuel retail price baselines (Petrol: ₹105.50/L, Diesel: ₹92.30/L, CNG: ₹85.00/kg).
- **`data/vehicle_data.csv`:** Standard vehicle fuel efficiency and displacement benchmarks.

### 4.2 Relational MySQL Database Tables
- **`users`:** User authentication, credentials (bcrypt hash), city, monthly $CO_2$ budget limit.
- **`daily_entries`:** Daily commute logs with vehicle characteristics, conditions, and calculated $CO_2$.
- **`trips`:** Granular trips recorded via GPS with start/end locations, degradation factors, eco-score, and anomaly flags.
- **`routes`:** Saved multi-route comparisons with distance, duration, and $CO_2$ metrics.
- **`leaderboard`:** User rankings, total distance, total $CO_2$, trips count, active daily streaks, and record streaks.
- **`smart_assessments`:** Vehicle health degradation reports, maintenance advice, and sustainability grades.
- **`user_rewards` & `reward_history`:** Green points balance, citizen tiers, unlocked badges, and point ledger.
- **`notifications`:** Real-time user alert records.
