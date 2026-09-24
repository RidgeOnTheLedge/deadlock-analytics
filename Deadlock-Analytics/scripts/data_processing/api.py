import requests

url = 'https://api.deadlock-api.com/v1/matches/metadata'

def fetch_matches(match_count):
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

    return response.json()