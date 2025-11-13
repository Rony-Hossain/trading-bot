# tools/hooks/pre_build.py
if __name__ == "__main__":
    import sys, json, pathlib
    print("[pre_build] args:", json.dumps(sys.argv[1:]))
    pathlib.Path(".pre_build_ran").write_text("ok")
