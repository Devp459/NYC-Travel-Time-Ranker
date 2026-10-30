import requests
import pandas as pd

APP_TOKEN = ""

DATASETS = {
    "Yellow Taxi": "irx2-vgm4",
    "High Volume FHV": "nt46-nv3c",
}
BASE = "https://data.cityofnewyork.us"


def get_first_rows(dataset_id, n=10):
    if APP_TOKEN:
        url = f"{BASE}/api/v3/views/{dataset_id}/query.json"
        body = {"query": f"SELECT * LIMIT {n}", "page": {"pageNumber": 1, "pageSize": n}}
        resp = requests.post(url, json=body, headers={"X-App-Token": APP_TOKEN}, timeout=60)
    else:
        url = f"{BASE}/resource/{dataset_id}.json"
        resp = requests.get(url, params={"$limit": n}, timeout=60)
    resp.raise_for_status()
    return pd.DataFrame(resp.json())


if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 250)
    for name, dataset_id in DATASETS.items():
        print(f"\n===== {name} (first 10 rows) =====")
        print(get_first_rows(dataset_id))
