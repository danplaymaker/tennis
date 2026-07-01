"""Quick diagnostic: fetch one live API response and print its shape."""
import json
import sys
import httpx

API_KEY = sys.argv[1] if len(sys.argv) > 1 else ""
if not API_KEY:
    print("Usage: python diagnose.py <api-key>")
    sys.exit(1)

resp = httpx.get(
    "https://api.api-tennis.com/tennis/",
    params={"method": "get_events", "event_type": "live", "APIkey": API_KEY},
    timeout=15,
)
data = resp.json()

print(f"success: {data.get('success')!r} (type: {type(data.get('success')).__name__})")
result = data.get("result", [])
print(f"result type: {type(result).__name__}")

if isinstance(result, list):
    print(f"events: {len(result)}")
    for i, e in enumerate(result[:3]):
        print(f"\n--- Event {i} ---")
        print(f"  event_key: {e.get('event_key')!r}")
        print(f"  event_first_player: {e.get('event_first_player')!r}")
        print(f"  event_second_player: {e.get('event_second_player')!r}")
        print(f"  event_home_team: {e.get('event_home_team')!r}")
        print(f"  event_away_team: {e.get('event_away_team')!r}")
        print(f"  event_status: {e.get('event_status')!r}")
        print(f"  event_serve: {e.get('event_serve')!r}")
        print(f"  event_service: {e.get('event_service')!r}")
        print(f"  event_live: {e.get('event_live')!r}")
        print(f"  event_game_result: {e.get('event_game_result')!r}")
        print(f"  event_final_result: {e.get('event_final_result')!r}")
        scores = e.get("scores")
        print(f"  scores type: {type(scores).__name__}, value: {json.dumps(scores)[:200] if scores else 'None'}")
        pbp = e.get("pointbypoint")
        print(f"  pointbypoint type: {type(pbp).__name__ if pbp is not None else 'None'}")
        if isinstance(pbp, list) and pbp:
            first = pbp[0]
            print(f"    [0] type: {type(first).__name__}, keys: {list(first.keys()) if isinstance(first, dict) else 'n/a'}")
            if isinstance(first, dict):
                games = first.get("games", [])
                if isinstance(games, list) and games:
                    print(f"    [0].games[0]: {json.dumps(games[0])[:300]}")
        stats = e.get("statistics")
        print(f"  statistics type: {type(stats).__name__ if stats is not None else 'None'}")
        if isinstance(stats, list) and stats:
            print(f"    [0]: {json.dumps(stats[0])[:200]}")
        # Print all top-level keys
        print(f"  ALL KEYS: {sorted(e.keys())}")
elif isinstance(result, dict):
    print(f"result keys: {sorted(result.keys())}")
    print(json.dumps(result, indent=2)[:500])
elif isinstance(result, str):
    print(f"result string: {result[:500]}")
else:
    print(f"result: {str(result)[:500]}")
