import json
from datetime import datetime, timezone
from pathlib import Path
import pyarrow as pa


def log_storage(project_root, raw_json):
    log_path = project_root / "data" / "raw" / "raw_data.log"

    stored_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    record_count = len(raw_json)

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"{stored_at} | stored matches.json | records={record_count}\n"
        )

def store_json(raw_json):
    try:
        project_root = Path(__file__).resolve().parents[2]
    except NameError:
        project_root = Path.cwd().parents[1]

    output_dir = project_root / "data" / "raw"

    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / "matches.json"

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(raw_json, f, indent=4)

    print(f"Replaced raw file: {file_path}")

    log_storage(project_root, raw_json)

def store_to_parquet(df, file_name):

    try:
        project_root = Path(__file__).resolve().parents[2]
    except:
        project_root = Path.cwd().parents[1]

    output_dir = project_root / "data" / "processed"

    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"{file_name}.parquet"

    table = pa.Table.from_pandas(df)
    df.to_parquet(file_path, engine='pyarrow')

    print(f"Stored {file_name} files to: {output_dir}")

