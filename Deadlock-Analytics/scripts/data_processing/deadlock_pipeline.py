# Should I move these?
import requests, json
import pandas as pd
from client import client
import json
from datetime import datetime, timezone
from pathlib import Path
import pyarrow as pa

url = 'https://api.deadlock-api.com/v1/matches/metadata'\

match_count = 200

print(f"Pulling {match_count} into a json file from api.deadlock-api.com...")

params = {
    "limit": match_count,  # Don't hard code rate limits
    "order_by": "start_time",
    "order_direction": "desc",
    "match_mode": "ranked",
    "include_info": "true",
    "include_more_info": "true",
    "include_objectives": "true",
    "include_mid_boss": "true",
    "include_player_info": "true",
    "include_player_final_stats": "true",
    "include_player_stats": "true",
    "include_player_items": "true",
    "include_player_death_details": "true",
    "hero_ids": "77",  # Only get hero ids for apollo
    "format": "json",
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()
matches_json = response.json()

print("Matches Pulled!")

print("Storing raw matches json")

try:
    project_root = Path(__file__).resolve().parents[2]
except NameError:
     project_root = Path.cwd().parents[1]

output_dir = project_root / "data" / "raw"

output_dir.mkdir(parents=True, exist_ok=True)

file_path = output_dir / "matches.json"

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(matches_json, f, indent=4)

print(f"Replaced raw file: {file_path}")

log_path = project_root / "data" / "raw" / "raw_data.log"

stored_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
record_count = len(matches_json)

with log_path.open("a", encoding="utf-8") as log_file:
    log_file.write(
        f"{stored_at} | stored matches.json | records={record_count}\n"
    )

print("Converting raw data into data frames...")

cli = client(matches_json)


print("Storing data frames into parquet...")
try:
    project_root = Path(__file__).resolve().parents[2]
except:
     project_root = Path.cwd().parents[1]

output_dir = project_root / "data" / "processed"

output_dir.mkdir(parents=True, exist_ok=True)

file_path = output_dir / "matches.parquet"

table = pa.Table.from_pandas(cli.df_matches)
cli.df_matches.to_parquet(file_path, engine='pyarrow')

print(f"Stored parquet files to: {output_dir}")


# # Next time add this to reload parequet files
#
# try:
#     project_root = Path(__file__).resolve().parents[2]
# except NameError:
#     project_root = Path.cwd().parents[1]
#
# file_path = project_root / "data" / "processed" / "matches.parquet"
#
# # 2. Load the parquet file back into pandas
# df_matches = pd.read_parquet(file_path, engine='pyarrow')
