"""Diagnostic: discover FlashLive API structure for tennis.

Usage:
    python diagnose_flashlive.py YOUR_RAPIDAPI_KEY

Get a free key at: https://rapidapi.com/tipsters/api/flashlive-sports
"""

import json
import sys

import httpx

HOST = "flashlive-sports.p.rapidapi.com"
BASE = f"https://{HOST}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python diagnose_flashlive.py YOUR_RAPIDAPI_KEY")
        print("Get a free key at: https://rapidapi.com/tipsters/api/flashlive-sports")
        sys.exit(1)

    api_key = sys.argv[1]
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": HOST,
    }

    with httpx.Client(headers=headers, timeout=15) as client:
        # 1. List all sports to find tennis sport_id
        print("=" * 60)
        print("STEP 1: DISCOVERING SPORT IDS")
        print("=" * 60)
        try:
            resp = client.get(f"{BASE}/v1/sports/list", params={"locale": "en_INT"})
            resp.raise_for_status()
            data = resp.json()
            sports = data.get("DATA", [])
            print(f"Found {len(sports)} sports:")
            tennis_id = None
            for s in sports:
                name = s.get("NAME", s.get("name", "?"))
                sid = s.get("ID", s.get("id", "?"))
                if "tennis" in str(name).lower():
                    tennis_id = str(sid)
                    print(f"  >>> {name}: sport_id={sid} <<<")
                else:
                    print(f"  {name}: sport_id={sid}")
            if not tennis_id:
                print("\nTennis not found! Full response:")
                print(json.dumps(data, indent=2)[:2000])
                return
        except Exception as ex:
            print(f"Error listing sports: {ex}")
            return

        # 2. Fetch live tennis events
        print(f"\n{'=' * 60}")
        print(f"STEP 2: LIVE TENNIS EVENTS (sport_id={tennis_id})")
        print("=" * 60)
        try:
            resp = client.get(
                f"{BASE}/v1/events/live",
                params={"sport_id": tennis_id, "locale": "en_INT"},
            )
            resp.raise_for_status()
            data = resp.json()
            top = data.get("DATA", [])
            print(f"Top-level DATA has {len(top)} items")

            all_events = []
            for i, item in enumerate(top[:5]):
                print(f"\n--- Tournament group {i} ---")
                print(f"  Keys: {sorted(item.keys())}")
                print(f"  NAME: {item.get('NAME', '?')}")
                print(f"  COUNTRY_NAME: {item.get('COUNTRY_NAME', '?')}")

                events = item.get("EVENTS", [])
                if events:
                    print(f"  EVENTS count: {len(events)}")
                    for j, e in enumerate(events[:3]):
                        all_events.append(e)
                        print(f"\n    Event {j}:")
                        print(f"      ALL KEYS: {sorted(e.keys())}")
                        for k in sorted(e.keys()):
                            v = e[k]
                            if not isinstance(v, (dict, list)):
                                print(f"      {k}: {v}")
                            elif isinstance(v, list) and len(v) < 5:
                                print(f"      {k}: {v}")
                elif "EVENT_ID" in item:
                    all_events.append(item)
                    print(f"  (Flat event, not grouped)")
                    for k in sorted(item.keys()):
                        v = item[k]
                        if not isinstance(v, (dict, list)):
                            print(f"  {k}: {v}")

            total = sum(len(item.get("EVENTS", [])) for item in top)
            if not total:
                total = len([i for i in top if "EVENT_ID" in i])
            print(f"\nTotal events across all tournaments: {total}")

        except Exception as ex:
            print(f"Error fetching live events: {ex}")
            import traceback
            traceback.print_exc()
            return

        # 3. Fetch detail for first event
        if all_events:
            eid = all_events[0].get("EVENT_ID", all_events[0].get("id"))
            if eid:
                print(f"\n{'=' * 60}")
                print(f"STEP 3: EVENT STATISTICS (event_id={eid})")
                print("=" * 60)
                try:
                    resp = client.get(
                        f"{BASE}/v1/events/statistics",
                        params={"event_id": eid, "locale": "en_INT"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        print(json.dumps(data, indent=2)[:3000])
                    else:
                        print(f"Status {resp.status_code}: {resp.text[:500]}")
                except Exception as ex:
                    print(f"Error: {ex}")

                print(f"\n{'=' * 60}")
                print(f"STEP 4: EVENT INCIDENTS (event_id={eid})")
                print("=" * 60)
                try:
                    resp = client.get(
                        f"{BASE}/v1/events/summary-incidents",
                        params={"event_id": eid, "locale": "en_INT"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        print(json.dumps(data, indent=2)[:3000])
                    else:
                        print(f"Status {resp.status_code}: {resp.text[:500]}")
                except Exception as ex:
                    print(f"Error: {ex}")
        else:
            print("\nNo live events to inspect detail for.")

    print(f"\n{'=' * 60}")
    print("DONE — copy-paste the output above so we can tune the provider.")
    print("=" * 60)


if __name__ == "__main__":
    main()
