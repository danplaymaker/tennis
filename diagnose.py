"""Quick diagnostic: fetch live API response and print its shape."""
import json
import sys
import httpx

API_KEY = sys.argv[1] if len(sys.argv) > 1 else ""
if not API_KEY:
    print("Usage: python3 diagnose.py <api-key>")
    sys.exit(1)

BASE = "https://api.api-tennis.com/tennis/"

for method in ["get_livescore", "get_events&event_type=live"]:
    print(f"\n{'='*60}")
    print(f"METHOD: {method}")
    print(f"{'='*60}")

    if "&" in method:
        parts = method.split("&")
        params = {"method": parts[0], "APIkey": API_KEY}
        for p in parts[1:]:
            k, v = p.split("=")
            params[k] = v
    else:
        params = {"method": method, "APIkey": API_KEY}

    resp = httpx.get(BASE, params=params, timeout=15)
    data = resp.json()

    print(f"success: {data.get('success')!r} (type: {type(data.get('success')).__name__})")
    result = data.get("result", [])
    print(f"result type: {type(result).__name__}")

    if isinstance(result, list):
        print(f"events: {len(result)}")
        for i, e in enumerate(result[:2]):
            print(f"\n--- Event {i} ---")
            print(f"  ALL KEYS: {sorted(e.keys())}")
            for key in sorted(e.keys()):
                val = e[key]
                if isinstance(val, (list, dict)):
                    val_str = f"{type(val).__name__}({len(val)})"
                    if isinstance(val, list) and val and isinstance(val[0], dict):
                        val_str += f" keys={sorted(val[0].keys())}"
                    elif isinstance(val, dict):
                        val_str += f" keys={sorted(val.keys())[:10]}"
                else:
                    val_str = repr(val)[:100]
                print(f"  {key}: {val_str}")
    elif isinstance(result, str):
        print(f"result string: {result[:500]}")
    else:
        print(f"result: {str(result)[:500]}")
