# tools/hooks/post_build.py
if __name__ == "__main__":
    import sys, json, pathlib
    print("[post_build] args:", json.dumps(sys.argv[1:]))
    # write into the dist folder if it exists
    dist = pathlib.Path("dist")
    if dist.exists():
        (dist / "_post_build_ran").write_text("ok")
