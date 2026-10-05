import requests, json
import pandas as pd


def bronze_matches(raw_matches):
    matches_df = pd.DataFrame(raw_matches)

    # Drop matches that were most likely bugged
    matches_df = matches_df[matches_df["rewards_eligible"].eq(True)]

    return matches_df


def silver_matches(bronze_matches_df):
    columns = [
        "match_id",
        "start_time",
        "winning_team",
        "duration_s",
        "match_outcome",
        "average_badge",
        "rewards_eligible"
    ]  # possibly add "banned_hero_ids"

    return bronze_matches_df[columns].copy()


def bronze_players(bronze_matches_df):
    df_bronze_players = pd.json_normalize(
        bronze_matches_df.to_dict('records'),
        record_path=['players'],
        meta=["match_id"]
    )

    return df_bronze_players[df_bronze_players['player_match_outcome'].isin(['Win', 'Loss'])]


def silver_players(df_bronze_players):
    # Consider adding back abandon_match_time_s and pregame_hero_id it seems you could check if they got there main hero or not.
    custom_final_stats = list(
        df_bronze_players.filter(
            regex="final_stats.custom|player_rank")
        .columns
    )

    drop_cols = [
        "abandon_match_time_s",
        "accolades",
        "hero_xp_rewards",
        "items",
        "stats",
        "death_details",
        "hero_build_id",
        "pregame_hero_id"
    ]

    drop_cols += custom_final_stats

    silver_player_df = df_bronze_players.drop(drop_cols, axis=1, errors='ignore')

    return silver_player_df


def bronze_stats(bronze_players_df):
    exploded_stats = (
        bronze_players_df[
            ['match_id', 'account_id', 'hero_id', 'stats', 'player_match_outcome']
        ].explode('stats')
        .reset_index(drop=True)
    )

    normalized_stats = pd.json_normalize(
        exploded_stats['stats']
    ).reset_index(drop=True)

    bronze_stats_df = pd.concat(
        [
            exploded_stats[
                ['match_id', 'account_id', 'hero_id', 'player_match_outcome']
            ],
            normalized_stats
        ], axis=1)

    bronze_stats_df = (bronze_stats_df.sort_values(["match_id", "account_id", "time_stamp_s"],
                                                   ascending=[True, True, True]).reset_index(drop=True))

    return bronze_stats_df


def silver_objectives(raw_df_matches):
    # Explode the lists into individual rows
    matches_objectives = raw_df_matches[["match_id", "objectives"]].explode("objectives").reset_index(drop=True)

    # Normalize the dictionaries AND preserve the original index alignment
    normalized_df = pd.json_normalize(matches_objectives['objectives'])

    # Join them safely without mismatched rows
    matches_objectives = matches_objectives[["match_id"]].join(normalized_df)
    return matches_objectives


def silver_items(bronze_players_df):
    silver_items_df = (
        bronze_players_df[['match_id', 'account_id', 'hero_id', 'items', 'player_match_outcome']]
        .explode('items')
        .dropna(subset=['items'])
        .reset_index(drop=True)
    )
    silver_items_df = silver_items_df.join(pd.json_normalize(silver_items_df['items'])).drop(columns='items')


    # Don't have a random api call in this class fix later
    response = requests.get('https://api.deadlock-api.com/v1/assets/items', timeout=30)
    response.raise_for_status()
    assets = pd.DataFrame(response.json())

    meta = (assets[['id', 'name', 'type', 'shopable']]
            .drop_duplicates('id')
            .rename(columns={'id': 'item_id', 'name': 'item_name'}))

    silver_items_df = silver_items_df.merge(meta, on='item_id', how='left')
    silver_items_df['shopable'] = silver_items_df['shopable'].eq(True)
    return silver_items_df



# def silver_items(df_players, df_stats):
#     bronze_silver_items_df = df_players[['match_id', 'account_id', 'hero_id', 'items', 'player_match_outcome']].explode(
#         'items').reset_index(drop=True)
#     bronze_silver_items_df = bronze_silver_items_df.join(pd.json_normalize(bronze_silver_items_df['items']))
# 
#     url = 'https://api.deadlock-api.com/v1/assets/items'
#     response = requests.get(url, timeout=30)
#     response.raise_for_status()
#     items = response.json()
# 
#     mapping = {}
#     for item in items:
#         if item['type'] == 'upgrade' and item.get('shopable', False):
#             mapping[item["id"]] = item["name"]
#             upgrade_id = item.get('upgrade_id')
# 
#     bronze_silver_items_df["item_name"] = bronze_silver_items_df["item_id"].map(mapping)
# 
#     bronze_silver_items_df = bronze_silver_items_df.dropna(subset=['game_time_s'])
#     # Fix the error of int64, which is because int65 cnat have Na but Int64 can
#     by_cols = ['account_id', 'match_id', 'hero_id', 'game_time_s', 'time_stamp_s']
#     for col in by_cols:
#         if col in bronze_silver_items_df.columns:
#             bronze_silver_items_df[col] = bronze_silver_items_df[col].astype("Int64")
#         if col in df_stats.columns:
#             df_stats[col] = df_stats[col].astype("Int64")
# 
#     # merge stats and items id by game time stamps of both
#     result = pd.merge_asof(
#         bronze_silver_items_df.sort_values('game_time_s'),
#         df_stats.sort_values('time_stamp_s'),
#         left_on='game_time_s',
#         right_on='time_stamp_s',
#         by=['account_id', 'match_id', 'hero_id'],
#         direction='nearest', )
# 
#     merged = result.drop(columns=['items', 'stats'])
# 
#     purchases_clean = merged[[
#         'match_id', 'account_id', 'hero_id',
#         'game_time_s', 'item_name', 'item_id', 'upgrade_id', 'sold_time_s',
#         'flags', 'imbued_ability_id', 'upgrade_info', 'net_worth', 'player_match_outcome'
#     ]]
#     purchases_clean_dropna = purchases_clean.dropna(subset=['item_name'])  # remove starting hero 'items'
#     return purchases_clean_dropna
