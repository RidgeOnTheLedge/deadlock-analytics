from storage import store_json, store_to_parquet
from api import fetch_matches
from transformations import (
    bronze_matches,
    bronze_players,
    silver_matches,
    silver_players,
)

def run_pipeline(match_count: int = 10) -> None:
    print(f"Pulling {match_count} into a json file from api.deadlock-api.com...")

    matches_json = fetch_matches(match_count)

    print("Matches Pulled!")
    print("Storing raw matches JSON...")

    store_json(matches_json)

    print("Converting raw data into data frames...")

    df_bronze_matches = bronze_matches(matches_json)
    df_silver_matches = silver_matches(df_bronze_matches)

    df_bronze_players = bronze_players(df_bronze_matches)
    df_silver_players = silver_players(df_bronze_players)

    print("Storing silver data frames into parquet...")

    store_to_parquet(df_silver_matches, "silver_matches")
    store_to_parquet(df_silver_players, "silver_players")

    print("Pipeline Complete")

    # # Incomplete
    # df_objectives = client.silver_objectives(df_bronze_matches)
    #
    # # Incomplete
    # df_stats = client.silver_stats(df_bronze_players)
    # df_items = client.silver_items(df_bronze_players, df_stats)

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
