"""Diagnostic: fetch SofaScore live tennis events and dump their shape."""
import json
import sys
import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
BASE = "https://api.sofascore.com/api/v1"


def main():
    with httpx.Client(headers=HEADERS, timeout=15) as client:
        # 1. Fetch all live tennis events
        print("=" * 60)
        print("LIVE TENNIS EVENTS")
        print("=" * 60)
        resp = client.get(f"{BASE}/sport/tennis/events/live")
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])
        print(f"Total live events: {len(events)}")

        # Show category breakdown
        cats = {}
        for e in events:
            cat = e.get("tournament", {}).get("category", {}).get("name", "?")
            cats[cat] = cats.get(cat, 0) + 1
        print(f"\nCategories: {dict(sorted(cats.items()))}")

        # Show first 3 events in detail
        for i, e in enumerate(events[:3]):
            print(f"\n--- Event {i} ---")
            print(f"  id: {e.get('id')}")
            home = e.get("homeTeam", {})
            away = e.get("awayTeam", {})
            print(f"  home: {home.get('name')} (id={home.get('id')})")
            print(f"  away: {away.get('name')} (id={away.get('id')})")
            t = e.get("tournament", {})
            print(f"  tournament: {t.get('name')}")
            print(f"  category: {t.get('category', {}).get('name')}")
            print(f"  status: {e.get('status', {}).get('description')}")
            print(f"  homeScore: {e.get('homeScore', {})}")
            print(f"  awayScore: {e.get('awayScore', {})}")
            print(f"  lastPeriod: {e.get('lastPeriod')}")
            print(f"  ALL KEYS: {sorted(e.keys())}")

        if not events:
            print("No live events right now.")
            return

        # 2. Fetch incidents (point-by-point) for first event
        eid = events[0]["id"]
        print(f"\n{'=' * 60}")
        print(f"INCIDENTS for event {eid}")
        print(f"{'=' * 60}")
        try:
            resp2 = client.get(f"{BASE}/event/{eid}/incidents")
            resp2.raise_for_status()
            inc_data = resp2.json()
            incidents = inc_data.get("incidents", [])
            print(f"Total incidents: {len(incidents)}")
            for inc in incidents[:10]:
                print(f"  {inc.get('incidentType', '?'):15} | "
                      f"home={inc.get('homeScore', '?')}-{inc.get('awayScore', '?')} | "
                      f"text={inc.get('text', '')[:50]}")
                if inc.get("incidentType") == "point":
                    print(f"    -> point details keys: {sorted(inc.keys())}")
        except Exception as ex:
            print(f"Error fetching incidents: {ex}")

        # 3. Fetch statistics for first event
        print(f"\n{'=' * 60}")
        print(f"STATISTICS for event {eid}")
        print(f"{'=' * 60}")
        try:
            resp3 = client.get(f"{BASE}/event/{eid}/statistics")
            resp3.raise_for_status()
            stat_data = resp3.json()
            stats = stat_data.get("statistics", [])
            print(f"Stat groups: {len(stats)}")
            for sg in stats[:2]:
                print(f"  period: {sg.get('period')}")
                for g in sg.get("groups", [])[:3]:
                    print(f"    group: {g.get('groupName')}")
                    for item in g.get("statisticsItems", [])[:5]:
                        print(f"      {item.get('name')}: {item.get('home')} / {item.get('away')}")
        except Exception as ex:
            print(f"Error fetching statistics: {ex}")


if __name__ == "__main__":
    main()
