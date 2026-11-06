# 01_clean_citibike

This notebook cleans the Citi Bike data for our project.
Right now it only covers October 2025. After cleaning, we have 4,713,105 good bike rides.

## What it does
1. Reads all the Citi Bike CSV files from the Databricks volume `/Volumes/workspace/default/citibike`.
2. Skips the JC- files, because those are Jersey City, not NYC.
3. Removes rides with no start or end location (15,689 rides).
4. Removes rides shorter than 1 minute or longer than 3 hours, because those are probably mistakes (3,105 rides).
5. Removes rides outside NYC (1 ride).
6. Adds 3 new columns: minutes (how long the ride took), start_hour (hour of the day, 0 to 23), and dow (day of the week).
7. Saves the clean data as a table called `workspace.default.citibike_clean`.

Row counts: 4,731,900 at the start, 4,713,105 at the end.

## How to run it
1. Download the Citi Bike CSV files from the Citi Bike data page.
2. In Databricks, make a volume called `citibike` (in workspace > default) and upload the CSVs.
3. Import this notebook and click Run all.

## What the clean table has
ride_id, rideable_type (classic or electric), started_at, ended_at, start and end station names and ids, start and end latitude and longitude, member_casual, minutes, start_hour, dow.

Note: dow counts 1 = Sunday up to 7 = Saturday.

## What you can do with it
- Match each ride's start and end point to a taxi zone, so we can compare bike, taxi and for-hire trips between the same two places.
- Study how long bike trips take for each pair of zones, hour and day.
- Keep only weekday rush hour (4 to 7 PM): dow between 2 and 6, and start_hour 16, 17 or 18.
- Find the typical (median) trip time for each pair of zones. This is our baseline.
- Compare classic and electric bikes, or members and casual riders.

## Things to know
- Only October 2025 so far. To add more months, upload their CSVs and run the notebook again.
- Each free Databricks account is separate, so you can't see my table. Run this notebook on your own account to make your own copy.
- We only have rides that really happened. Some pairs of zones may have very few rides or none.
