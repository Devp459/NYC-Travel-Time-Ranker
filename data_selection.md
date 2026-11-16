# Data Selection: NYC Travel-Time Mode Ranker

Team 404: Dhru Patel, Dev Patel, Vaibhav Bharati. CS 483, Fall 2026.

**Verified** means we measured it ourselves from the source files or our notebooks (checked 2026-11-11). **Estimate** means we have not confirmed it yet.

---

## 1. Project Goal

In NYC you can get from A to B by yellow taxi, Uber/Lyft, or Citi Bike. Map apps give one route and one time. They do not tell you which mode is usually fastest at a given hour, or how much the time changes from day to day.

**Research question:** Between two NYC taxi zones on weekdays, 4 to 7 PM, which mode is fastest, and how much does its travel time vary?

**Goal:** Type in two places and get all three modes ranked from fastest to slowest, each with a time range (for example, "12 to 18 min").

**Why it is worth doing:** People plan for bad days, not average days, so a range is more useful than one number. To get a reliable range for every zone pair and hour, you need millions of real trips.

---

## 2. Data Sources

| Dataset | Published by | Link | How we get it |
|---|---|---|---|
| 2025 High Volume FHV trips (Uber, Lyft) | NYC Taxi & Limousine Commission (TLC) | [NYC OpenData nt46-nv3c](https://data.cityofnewyork.us/Transportation/2025-High-Volume-FHV-Trip-Data/nt46-nv3c/about_data) | API, or monthly Parquet files from the [TLC website](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) |
| 2025 Yellow Taxi trips | NYC TLC | [NYC OpenData irx2-vgm4](https://data.cityofnewyork.us/Transportation/2025-Yellow-Taxi-Trip-Data/irx2-vgm4/about_data) | Same as above |
| 2025 Citi Bike trips | Lyft (runs Citi Bike) | [citibikenyc.com/system-data](https://citibikenyc.com/system-data) | Monthly ZIP files of CSVs |
| Automated Traffic Volume Counts | NYC Dept. of Transportation | [NYC OpenData 7ym2-wayt](https://data.cityofnewyork.us/Transportation/Automated-Traffic-Volume-Counts/7ym2-wayt/about_data) | API |
| Taxi zone map and lookup | NYC TLC | [taxi_zones.zip](https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip), [lookup CSV](https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv) | Direct download |

**License:** All sources are free and public. NYC data follows the [NYC OpenData Terms of Use](https://opendata.cityofnewyork.us/overview/#termsofuse). The [Citi Bike license](https://citibikenyc.com/data-sharing-policy) lets us analyze the data, but we may not re-share the raw files. So our GitHub repository holds code only, not data.

---

## 3. Dataset Description

| Source | Rows (2025) | Size | Files | Status |
|---|---|---|---|---|
| FHV (Uber/Lyft) | 243,589,684 | 5.96 GB (Parquet) | 12 monthly files | verified |
| Yellow Taxi | 48,722,602 | 0.83 GB (Parquet) | 12 monthly files | verified |
| Citi Bike | 15,569,024 for 4 months; about 46M for the full year | 8.9 GB (zipped CSV) | 12 ZIPs, each holding 3 to 5 CSVs | 4 months verified, full year an estimate |
| Traffic counts | 82,368 | about 20 MB | 1 table | verified |
| **Total** | **about 338 million trips** | **about 15.7 GB compressed** | | |

**Main fields:**
- **Taxi and FHV:** pickup and drop-off time, pickup and drop-off zone ID, distance, fare.
- **Citi Bike:** start and end time, start and end latitude/longitude, bike type, member or casual rider.
- **Traffic:** road segment, date, 15-minute time slot, number of vehicles, location point.

**One dataset or many?** Many. We join them by **taxi zone** and **hour**. Taxi and FHV trips already have zone IDs. Bike trips and traffic counters only have map coordinates, so we work out which zone each point falls in (`03_map_to_zones`). Everything ends up in one table, `trips_zoned`, with the same columns for every mode.

**What we use so far:**
- **Citi Bike:** 4 months (Jan, Apr, Jul, Oct).
- **Taxi and FHV:** a sample from the API (every 3rd day, at most 1,000 trips per hour). That gives about 2.6M taxi trips and 2.8M FHV trips, which is only about 1 to 5% of the data. Next we will load the full Parquet files.

---

## 4. The 5 Vs

### Volume
- **What we have:** about 338 million trips (about 15.7 GB compressed). FHV alone has 243.6M rows, and a single month of it is about 21M rows.
- **Why it is hard:**
  - The full year does not fit in a laptop's memory.
  - The NYC API is too slow. Just counting the FHV rows timed out after 10 minutes.
  - We need percentiles for every zone pair, hour and mode: up to about 5 million groups. That needs Spark.
- **Plan:** Process the full 2025 year in Spark, one month at a time, reading only the columns we need.

### Velocity
- **What we have:**
  - Trips happen all the time (about 800,000 taxi and FHV trips a day), but they are published in batches.
  - TLC releases a new month about 2 months later, and the 2025 tables are now final.
  - Citi Bike releases monthly. Traffic counts update about every 6 months.
- **Design:** Batch processing is enough. Our question is about typical travel times, which change slowly, so we don't need real-time streaming.
- **Plan:** New months can be added by loading the new files and re-running the notebooks for that month.

### Variety
- **What we have:**

| Source | Format | Location given as |
|---|---|---|
| Taxi / FHV | Parquet (or JSON from the API) | Taxi zone ID |
| Citi Bike | CSV inside ZIPs (sometimes a ZIP inside a ZIP) | Latitude / longitude |
| Traffic | JSON from the API | X/Y in feet (NY State Plane) |
| Taxi zones | Shapefile (map polygons) + CSV | Polygons in feet |

- **Challenges:**
  - **Three different location formats.** We convert all of them to taxi zones.
  - **Different column names for the same thing** (`tpep_pickup_datetime`, `pickup_datetime`, `started_at`). We rename them into one schema.
  - **Different time detail:** individual trips vs 15-minute traffic counts. We add traffic up to vehicles per hour.
  - **Points just outside every zone.** A few bike docks on piers and traffic counters on bridges fall outside the zone map, so we match them to the nearest zone.

### Veracity
- **Who publishes it:** Official city agencies (TLC, DOT) and Citi Bike. The data is well documented, but trips are reported by the companies and not checked one by one.
- **Problems we found** (October 2025, full month):

| Problem | Yellow Taxi (4.43M trips) | FHV (21.3M trips) |
|---|---|---|
| Passenger count missing | 22.4% | n/a |
| Fare zero or negative | 7.3% | 0.15% |
| Distance = 0 | 2.8% | 0.01% |
| Drop-off before or at pickup | 1.5% | about 0% |
| Unknown zone (264/265) | 0.8% | 4.6% |
| Duplicate rows | 410 | 15 |

- **Other problems:**
  - **Citi Bike:** 0.35% of rides have no end location. Jersey City files are mixed in with NYC.
  - **Traffic:** only 101 roads were counted in 2025, on sample days only.
  - **Two copies disagree:** the OpenData taxi table has 1.4% fewer 2025 rows than TLC's own files.
- **Bias:**
  - Bike riders may be riding for fun, not commuting.
  - Times start at pickup, so waiting for a car or walking to a dock is not counted.
  - Some outer-borough zone pairs have very few trips.
- **Cleaning:** We use the same rules for every mode:
  - Trip length from 1 to 180 minutes.
  - Zones 1 to 263 only.
  - Pickup in 2025.
  - Distance and fare above 0.
  - Speed from 0.5 to 80 mph.
  - Duplicates removed.

### Value
- **Problem:** Tell people which mode is fastest between two places, and how sure that answer is.
- **Who benefits:** Commuters, people with a deadline (airport, work), and city planners who want to see where biking beats driving at rush hour.
- **Questions we will answer:**
  1. For a zone pair and hour, what are the typical and the 10th to 90th percentile travel times for each mode?
  2. Which mode is fastest, and how often?
  3. Where does Citi Bike beat taxi or Uber/Lyft in the evening rush?
  4. Does road traffic explain slower trips?
- **How we will measure success:**
  - **MAE (minutes):** our model must beat a simple median baseline.
  - **Coverage:** about 80% of real trips should fall inside our predicted range.
  - **Ranking accuracy:** how often our "fastest mode" matches the real fastest mode.
- **First results** (median baseline trained on Jan, Apr and Jul, tested on October, weekdays 4 to 7 PM):

| Mode | Test trips | MAE (min) | Inside 10th to 90th percentile range |
|---|---|---|---|
| Bike | 978,821 | 3.89 | 80.9% |
| Taxi | 20,505 | 6.81 | 69.9% |
| FHV | 23,099 | 9.14 | 75.5% |

FHV does worst because we have only used about 1% of its trips, so most zone pairs have too few examples. Using all 243M FHV trips should fix this, which is why the project needs Big Data tools.

---

## 5. Data Preparation

| Task | Status |
|---|---|
| Unzip Citi Bike files and skip Jersey City | Done (4 months) |
| Clean Citi Bike | Done (4 months) |
| Load and clean traffic counts | Done |
| Match every source to taxi zones; build hourly traffic per zone | Done |
| Clean taxi and FHV (API sample) | Done |
| Median baseline | Done |
| Load full taxi and FHV Parquet files in Spark | To do |
| Load the other 8 Citi Bike months | To do |
| Build features and train the quantile model | To do |

**Expected challenges:**
- **Free Databricks has limited compute.** We may need to run one month at a time.
- **Taxi cleaning drops too much.** It currently drops rows with a missing passenger count, which is 22% of taxi trips, even though we don't need that column. We will fix this.
- **Column names don't match across notebooks.** Everyone must agree on the column names of the cleaned tables.
- **Zone pairs with too few trips.** We need a fallback, such as borough level, and a minimum trip count.

---

## 6. Limitations and Risks

| Limitation | Effect | What we will do |
|---|---|---|
| The data is historical (2025) | Can't predict today's accidents or weather | Show "typical" times; add new months later |
| Riders choose their mode | "Bike is fastest" may partly reflect who bikes | Compare only the same zone pair and hour; use medians |
| Pickup-to-drop-off only | Wait and walk time are not counted | Say this clearly in the app |
| Few traffic counters | Traffic is a weak feature | Use a borough-level fallback; test whether it helps |
| Citi Bike barely covers some boroughs | Few bike results there | Show "not enough data" instead of guessing |
| Free compute limits | Big jobs may be slow | Process by month, use only the needed columns |
