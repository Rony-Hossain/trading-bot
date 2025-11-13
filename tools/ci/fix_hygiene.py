# tools/ci/fix_hygiene.py
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMOJI_RE = re.compile(r'[\U0001F300-\U0001FAFF]')
CTRL_RE  = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F]')  # keep \t,\n,\r

def iter_py(paths):
    seen=set()
    for base in paths:
        if not base.exists(): continue
        for p in base.rglob("*.py"):
            if "__pycache__" in p.parts: continue
            rp=p.resolve()
            if rp in seen: continue
            seen.add(rp); yield p

def clean_text(text: str, strip_emojis: bool):
    changed=False
    # Remove leading BOM (U+FEFF)
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff"); changed=True
    # Normalize CRLF → LF (optional; keep CRLF if you prefer)
    # text = text.replace("\r\n","\n")
    # Strip trailing whitespace per line
    lines = text.splitlines(keepends=False)
    new_lines=[]
    for ln in lines:
        nl = ln.rstrip()
        if nl!=ln: changed=True
        new_lines.append(nl)
    text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
    # Remove control chars (except \t,\n,\r)
    if CTRL_RE.search(text):
        text = CTRL_RE.sub("", text); changed=True
    # Optional emoji removal (QuantConnect hates these)
    if strip_emojis and EMOJI_RE.search(text):
        text = EMOJI_RE.sub("", text); changed=True
    return text, changed

def main():
    ap=argparse.ArgumentParser(description="Fix BOM, trailing spaces, controls; optionally remove emojis.")
    ap.add_argument("--paths", default="src,config", help="Comma-separated roots")
    ap.add_argument("--strip-emojis", action="store_true")
    args=ap.parse_args()

    roots=[ROOT/p.strip() for p in args.paths.split(",") if p.strip()]
    fixed=0
    for p in iter_py(roots):
        txt = p.read_text(encoding="utf-8", errors="replace")
        new, changed = clean_text(txt, args.strip_emojis)
        if changed:
            p.write_text(new, encoding="utf-8")
            print(f"fixed: {p}")
            fixed+=1
    print(f"Done. Files modified: {fixed}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
