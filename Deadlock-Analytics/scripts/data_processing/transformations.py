import requests, json
import pandas as pd

def bronze_matches(json_matches):
    matches_df = pd.DataFrame(json_matches)

    # Drop matches that were most likely bugged
    matches_df = matches_df[matches_df["rewards_eligible"] == True]

    return matches_df

def silver_matches(raw_df_matches):
    keep_columns = ["match_id", "start_time", "winning_team", "duration_s", "match_outcome",
                    "average_badge", "rewards_eligible"]  # possibly add "banned_hero_ids"

    silver_matches = raw_df_matches[keep_columns]
    return silver_matches

def bronze_players(raw_df_matches):
    df_bronze_players = pd.json_normalize(raw_df_matches.to_dict('records'), record_path=['players'],
                                          meta=["match_id"])

    df_bronze_players = df_bronze_players[df_bronze_players['player_match_outcome'].isin(['Win', 'Loss'])]
    return df_bronze_players

def silver_players(df_bronze_players):
    # Consider adding back abandon_match_time_s and pregame_hero_id it seems you could check if they got there main hero or not.
    custom_final_stats = list(df_bronze_players.filter(regex="final_stats.custom|player_rank").columns)
    drop_cols = ["abandon_match_time_s", "accolades", "hero_xp_rewards", "items", "stats", "death_details",
                 "hero_build_id", "pregame_hero_id"]

    final_drop_cols = drop_cols + custom_final_stats
    silver_player_df = df_bronze_players.drop(final_drop_cols, axis=1, errors='ignore')

    return silver_player_df

def silver_objectives(raw_df_matches):
    # Explode the lists into individual rows
    matches_objectives = raw_df_matches[["match_id", "objectives"]].explode("objectives").reset_index(drop=True)

    # Normalize the dictionaries AND preserve the original index alignment
    normalized_df = pd.json_normalize(matches_objectives['objectives'])

    # Join them safely without mismatched rows
    matches_objectives = matches_objectives[["match_id"]].join(normalized_df)
    return matches_objectives

def silver_stats(df_players):
    df_stats =  df_players[['match_id', 'account_id', 'hero_id', 'stats']].explode('stats')
    normalized_df = pd.json_normalize(df_stats['stats'])
    df_stats = df_stats.join(normalized_df)
    return df_stats

def silver_items(df_players, df_stats):
    items_df = df_players[['match_id', 'account_id', 'hero_id', 'items', 'player_match_outcome']].explode('items').reset_index(drop=True)
    items_df = items_df.join(pd.json_normalize(items_df['items']))

    url = 'https://api.deadlock-api.com/v1/assets/items'
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    items = response.json()

    mapping = {}
    for item in items:
        if item['type'] == 'upgrade' and item.get('shopable', False):
            mapping[item["id"]] = item["name"]
            upgrade_id = item.get('upgrade_id')

    items_df["item_name"] = items_df["item_id"].map(mapping)


    items_df = items_df.dropna(subset=['game_time_s'])
    # Fix the error of int64, which is because int65 cnat have Na but Int64 can
    by_cols = ['account_id', 'match_id', 'hero_id', 'game_time_s', 'time_stamp_s']
    for col in by_cols:
        if col in items_df.columns:
            items_df[col] = items_df[col].astype("Int64")
        if col in df_stats.columns:
            df_stats[col] = df_stats[col].astype("Int64")

    # merge stats and items id by game time stamps of both
    result = pd.merge_asof(
        items_df.sort_values('game_time_s'),
        df_stats.sort_values('time_stamp_s'),
        left_on='game_time_s',
        right_on='time_stamp_s',
        by=['account_id', 'match_id', 'hero_id'],
        direction='nearest', )

    merged = result.drop(columns=['items', 'stats'])

    purchases_clean = merged[[
        'match_id', 'account_id', 'hero_id',
        'game_time_s', 'item_name', 'item_id', 'upgrade_id', 'sold_time_s',
        'flags', 'imbued_ability_id', 'upgrade_info', 'net_worth', 'player_match_outcome'
    ]]
    purchases_clean_dropna = purchases_clean.dropna(subset=['item_name']) # remove starting hero 'items'
    return purchases_clean_dropna

