import os, json, urllib.request, sys

def _slack_post(text: str) -> None:
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        return
    try:
        data = json.dumps({"text": text}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5).read()
    except Exception as e:
        print(f"[alerts] Slack notify failed: {e}", file=sys.stderr)

def notify_extreme(symbol: str, z: float, volx: float, direction: str, avwap_bps: float | None = None) -> None:
    tail = f" | aVWAP {avwap_bps:.0f} bps" if avwap_bps is not None else ""
    msg = f"EXTREME ⏱ {symbol}  z={z:.2f}  vol≈{volx:.1f}x  dir={direction}{tail}"
    print(msg, flush=True)
    _slack_post(msg)

def ask_user_to_confirm(prompt: str = "Confirm trade? (yes/no): ") -> bool:
    # Always ask in console; Slack is FYI only.
    ans = input(prompt).strip().lower()
    return ans in ("y", "yes")
