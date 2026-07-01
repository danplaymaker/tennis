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
                if "tennis" in str(name).lower() and "table" not in str(name).lower():
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

        # 2. Try multiple endpoint paths to find live events
        print(f"\n{'=' * 60}")
        print(f"STEP 2: FINDING LIVE EVENTS ENDPOINT (sport_id={tennis_id})")
        print("=" * 60)

        endpoints = [
            ("/v1/events/live-list", {"sport_id": tennis_id, "locale": "en_INT"}),
            ("/v1/events/live", {"sport_id": tennis_id, "locale": "en_INT"}),
            ("/v1/events/list", {"sport_id": tennis_id, "locale": "en_INT",
                                 "indent_days": "0", "timezone": "0"}),
        ]

        all_events = []
        working_endpoint = None

        for path, params in endpoints:
            try:
                resp = client.get(f"{BASE}{path}", params=params)
                print(f"\n  {path} -> {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    top = data.get("DATA", [])
                    print(f"    DATA has {len(top)} items")
                    if top:
                        working_endpoint = path
                        print(f"    First item keys: {sorted(top[0].keys()) if isinstance(top[0], dict) else type(top[0])}")

                        for i, item in enumerate(top[:3]):
                            if not isinstance(item, dict):
                                continue
                            events = item.get("EVENTS", [])
                            if events:
                                print(f"\n    Tournament: {item.get('NAME', '?')}")
                                print(f"    Country: {item.get('COUNTRY_NAME', '?')}")
                                print(f"    Events: {len(events)}")
                                for j, e in enumerate(events[:2]):
                                    all_events.append(e)
                                    print(f"\n      Event {j} keys: {sorted(e.keys())}")
                                    for k in sorted(e.keys()):
                                        v = e[k]
                                        if not isinstance(v, (dict, list)):
                                            print(f"        {k}: {v}")
                            elif "EVENT_ID" in item or "HOME_NAME" in item:
                                all_events.append(item)
                                print(f"\n    Flat event keys: {sorted(item.keys())}")
                                for k in sorted(item.keys()):
                                    v = item[k]
                                    if not isinstance(v, (dict, list)):
                                        print(f"      {k}: {v}")

                        total = sum(len(it.get("EVENTS", [])) for it in top if isinstance(it, dict))
                        if not total:
                            total = len([it for it in top if isinstance(it, dict) and ("EVENT_ID" in it or "HOME_NAME" in it)])
                        print(f"\n    Total events: {total}")
                        break
                else:
                    print(f"    Body: {resp.text[:200]}")
            except Exception as ex:
                print(f"    Error: {ex}")

        if not working_endpoint:
            print("\nNo working endpoint found!")
            return

        print(f"\n>>> WORKING ENDPOINT: {working_endpoint} <<<")

        # 3. Fetch statistics for first event
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

                # Also try points history (might have point-by-point for tennis)
                print(f"\n{'=' * 60}")
                print(f"STEP 5: EVENT POINTS HISTORY (event_id={eid})")
                print("=" * 60)
                try:
                    resp = client.get(
                        f"{BASE}/v1/events/points-history",
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
            print("\nNo events found to inspect.")

    print(f"\n{'=' * 60}")
    print("DONE — paste output above so we can tune the provider.")
    print("=" * 60)


if __name__ == "__main__":
    main()
