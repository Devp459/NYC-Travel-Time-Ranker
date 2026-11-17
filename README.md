# NYC Travel-Time Mode Ranker

Pick two places in New York City and get taxi, Uber/Lyft and Citi Bike ranked from fastest to slowest for a weekday evening trip, each with a time range such as "12 to 18 min".

Team 404: Dhru Patel, Dev Patel, Vaibhav Bharati.

## The question

> Between two NYC taxi zones on weekdays, 4 to 7 PM, which mode is fastest, and how much does its travel time vary?

Map apps give one route and one time. They don't say which mode is usually fastest at a given hour, or how much the time changes from day to day. We learn that from millions of real 2025 trips, so the answer comes with a range, not a single number.

## Progress

**Setup**
- [x] Create the Git repo and add the instructor and TA
- [x] Share the teamwork agreement and task board with the instructor and TA
- [x] Pick the weekly meeting time and the group chat

**Data ready**
- [x] Download and clean 2025 High Volume FHV and Yellow Taxi trips
- [x] Download and clean 2025 Citi Bike NYC trips (4 months so far)
- [x] Load traffic counts and map every source to taxi zones

**Model built**
- [x] Build features and the baseline (historical median)
- [x] Train the quantile gradient-boosted model (p10, p50 and p90 for bike, taxi and FHV)
- [ ] Set up evaluation: time-based split, MAE, interval coverage

**Ranker live**
- [ ] Ranking logic and prediction output
- [ ] App interface: two-location input and results
- [ ] Map and charts


## Results so far

Train on the earlier months, test on October, weekdays 4 to 7 PM. "Inside range" is how often the real trip time fell between the predicted 10th and 90th percentile (the target is about 80%).

| Mode | Model | Test trips | MAE (min) | Inside range |
|---|---|---|---|---|
| Bike | Median baseline | 978,821 | 3.89 | 80.9% |
| Bike | Gradient-boosted model | 978,821 | 3.63 | 81.8% |
| Taxi | Median baseline | 20,505 | 6.81 | 69.9% |
| FHV | Median baseline | 23,099 | 9.14 | 75.5% |

Taxi and FHV model results will be added once the evaluation is done. The taxi and FHV numbers are low-sample for now because we only pulled about 1 to 5% of those trips.

## Data

| Dataset | Published by | Used for |
|---|---|---|
| 2025 High Volume FHV trips | NYC TLC (NYC OpenData `nt46-nv3c`) | Uber/Lyft trip times |
| 2025 Yellow Taxi trips | NYC TLC (NYC OpenData `irx2-vgm4`) | Taxi trip times |
| 2025 Citi Bike trips | Lyft, [citibikenyc.com/system-data](https://citibikenyc.com/system-data) | Bike trip times |
| Automated Traffic Volume Counts | NYC DOT (NYC OpenData `7ym2-wayt`) | Road traffic by zone and hour |
| Taxi zone map and lookup | NYC TLC | Joining every source by taxi zone |

About 338 million trips in total (about 15.7 GB compressed). Details, checks and limits are in `data_selection.md`.

**No data is stored in this repo.** The Citi Bike license doesn't allow re-sharing the raw files, so the repo holds code only.

## How it works

1. **Build a travel-time history.** Clean each source, give every trip a pickup and dropoff taxi zone, and put them in one `trips_zoned` table with the same columns for every mode.
2. **Predict travel time.** For each mode, train p10, p50 and p90 models (LightGBM) on zone pair, hour, day of week, zone locations and distance, and traffic volume.
3. **Rank and show.** For a pair of places, predict all three modes, sort by the p50 time, and show the p10 to p90 range.

## Repo layout

```
clean_taxi_fhv.ipynb               Pull and clean Taxi and FHV trips from the NYC OpenData API
data_cleaning/
  00_unzip_citibike.ipynb          Unzip Citi Bike files, skip Jersey City
  01_clean_citibike.ipynb          Clean Citi Bike trips
  02_load_traffic_counts.ipynb     Load and clean 2025 traffic counts
  03_map_to_zones.ipynb            Map every source to taxi zones, build trips_zoned
  04_bike_features_baseline.ipynb  Bike features and the median baselines
  05_load_taxi_fhv.ipynb           Load the clean Taxi and FHV CSVs as tables
modeling/
  06_train_quantile_gbm.ipynb      Train and save the quantile models
preview_datasets.py                Peek at the first rows of the API datasets
```

## How to run

Everything runs in Databricks as notebooks. Each team member runs the notebooks in their own workspace, on the same datasets. Run them in this order:

1. `00_unzip_citibike`, then `01_clean_citibike`
2. `02_load_traffic_counts`
3. `clean_taxi_fhv` (writes `yellow_clean.csv` and `fhv_clean.csv` to the volume)
4. `05_load_taxi_fhv` (loads those files as tables)
5. `03_map_to_zones` (builds `trips_zoned` and the traffic tables)
6. `04_bike_features_baseline` (the last cell builds the baselines for all modes)
7. `06_train_quantile_gbm`

Check the schema and volume names at the top of each notebook. Notebook 03 reads the taxi and FHV tables from `YELLOW_TABLE` and `FHV_TABLE`, so these must point to where you loaded them.

Notebook 06 saves 9 models (`<mode>_q10`, `_q50`, `_q90`), a `model_spec.json`, and two lookup files (`zone_features.csv`, `traffic_features.csv`) to a volume folder. The app needs all of them.

## Tools and workflow

- **Databricks** (Free Edition) with PySpark and Delta tables for processing
- **LightGBM** for the quantile models
- **GitHub** for code and documents (data is not stored there)
- **Google Sheets** to track tasks
- **Google Drive** to share dataset and model files between team members

## 
