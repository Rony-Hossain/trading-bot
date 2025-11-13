import json
import os
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

class DeployCoreTests(unittest.TestCase):
    def setUp(self):
        # Create temp repo
        self.tmp = Path(tempfile.mkdtemp(prefix="deploy-core-test-")).resolve()

        # Project layout
        (self.tmp / "tools" / "hooks").mkdir(parents=True, exist_ok=True)
        (self.tmp / "src" / "components").mkdir(parents=True, exist_ok=True)
        (self.tmp / "config").mkdir(parents=True, exist_ok=True)

        # Minimal sources
        (self.tmp / "src" / "main.py").write_text(textwrap.dedent("""
            def Initialize():
                pass

            def OnData(data):
                pass

            # Big function to trigger split in tests when max_file_size is small
            def big_block():
                s = ""
                for i in range(2000):
                    s += str(i)
                return s
        """).strip() + "\n", encoding="utf-8")

        (self.tmp / "config" / "config.py").write_text("SETTING = 1\n", encoding="utf-8")

        (self.tmp / "src" / "components" / "dummy_strategy.py").write_text(textwrap.dedent("""
            def helper():
                return 42
        """).strip() + "\n", encoding="utf-8")

        # Hooks (write markers)
        (self.tmp / "tools" / "hooks" / "pre_build.py").write_text(textwrap.dedent("""
            if __name__ == "__main__":
                import sys, pathlib
                pathlib.Path(".pre_marker").write_text("pre-ran")
                print("PRE:", " ".join(sys.argv[1:]))
        """).strip() + "\n", encoding="utf-8")

        (self.tmp / "tools" / "hooks" / "post_build.py").write_text(textwrap.dedent("""
            if __name__ == "__main__":
                import sys, pathlib
                out = pathlib.Path("dist") / "quantconnect" / "_post_marker"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text("post-ran")
                print("POST:", " ".join(sys.argv[1:]))
        """).strip() + "\n", encoding="utf-8")

        # A small max_file_size to force splitting main.py
        self.platforms_path = self.tmp / "tools" / "platforms.json"
        self.platforms_path.write_text(json.dumps({
            "platforms": {
                "quantconnect": {
                    "name": "QuantConnect",
                    "flatten": True,
                    "max_file_size": 300,               # tiny to force split
                    "generate_upload_order": True,
                    "bundle_single_file": False,
                    "char_restrictions": [r"[\\U0001F300-\\U0001FAFF]"],
                    "file_order_priority": ["main.py", "config.py"],
                    "supports_packages": False,
                    "output_dir_name": "quantconnect",
                    "pre_build_script": "tools/hooks/pre_build.py",
                    "pre_build_args": ["--stage", "pre"],
                    "post_build_script": "tools/hooks/post_build.py",
                    "post_build_args": ["--stage", "post"],
                    "hook_timeout_sec": 60
                },
                "backtrader": {
                    "name": "Backtrader",
                    "flatten": False,
                    "max_file_size": None,
                    "generate_upload_order": False,
                    "bundle_single_file": True,
                    "char_restrictions": [],
                    "file_order_priority": [],
                    "supports_packages": True,
                    "output_dir_name": "backtrader_build",
                    "pre_build_script": None,
                    "post_build_script": None,
                    "hook_timeout_sec": 60
                }
            }
        }, indent=2), encoding="utf-8")

        # Ensure our tools/ is importable
        self.tools_dir = (Path(__file__).resolve().parents[1])
        # In CI the test file may be run from repo root; here ensure dynamic
        sys.path.insert(0, str(self.tools_dir))
        # If running these tests outside repo, fall back to current implementation
        try:
            import deploy_core  # noqa: F401
        except Exception:
            # copy provided deploy_core.py from real repo into temp tools dir if needed
            pass
        import deploy_core as dc  # re-import to bind now
        self.dc = dc  # save

    def tearDown(self):
        try:
            shutil.rmtree(self.tmp, ignore_errors=True)
        except Exception:
            pass
        # cleanup sys.path entry for this run
        try:
            sys.path.remove(str(self.tools_dir))
        except ValueError:
            pass

    def test_build_quantconnect_with_hooks_and_split(self):
        dc = self.dc

        # Run build (live, not dry-run), override hook args from CLI-equivalent
        result = dc.build_for_platform(
            root_dir=self.tmp,
            platform="quantconnect",
            platform_config=self.platforms_path,
            dry_run=False,
            force=True,
            minify=True,          # exercise optimizer
            tree_shake=False,
            bundle=False,
            pre_args_override=["--stage", "pre-override"],
            post_args_override=["--stage", "post-override"],
        )

        self.assertTrue(result["success"], msg=f"errors: {result['stats']['errors']}")
        outdir = Path(result["root"])
        self.assertTrue(outdir.exists(), "dist/quantconnect should exist")

        # Hooks ran?
        self.assertTrue((self.tmp / ".pre_marker").exists(), "pre hook should write marker")
        self.assertTrue((outdir / "_post_marker").exists(), "post hook should write marker in dist")

        # UPLOAD_ORDER exists (QC)
        self.assertTrue((outdir / "UPLOAD_ORDER.txt").exists(), "UPLOAD_ORDER.txt should be created")

        # Split occurred on main.py (due to tiny max_file_size)
        parts = sorted([p.name for p in outdir.glob("main_part*.py")])
        self.assertTrue(len(parts) >= 1, "main_part*.py should exist after split")

        # Facade exists and imports parts
        facade = outdir / "main.py"
        self.assertTrue(facade.exists(), "facade main.py should be created")
        txt = facade.read_text(encoding="utf-8")
        self.assertIn("from main_part", txt, "facade should import split parts")

        # Stats sanity
        stats = result["stats"]
        self.assertGreater(stats["files_processed"], 0)
        self.assertGreaterEqual(stats["files_split"], 1)
        self.assertIsInstance(stats["warnings"], list)
        self.assertIsInstance(stats["errors"], list)

    def test_clean_build_and_cache_clean(self):
        dc = self.dc
        # create a fake cache
        cache_dir = self.tmp / ".build_cache"
        cache_dir.mkdir(exist_ok=True)
        (cache_dir / "dummy").write_text("x", encoding="utf-8")

        # build once to create dist
        dc.build_for_platform(
            root_dir=self.tmp,
            platform="quantconnect",
            platform_config=self.platforms_path,
            dry_run=False,
            force=True
        )
        self.assertTrue((self.tmp / "dist" / "quantconnect").exists())

        # clean both dist and cache
        removed = dc.clean_build(
            root_dir=self.tmp,
            platform="quantconnect",
            platform_rules=None,
            cache_clean=True,
            cache_dir=cache_dir
        )
        self.assertTrue(removed)
        self.assertFalse((self.tmp / "dist" / "quantconnect").exists())
        self.assertFalse(cache_dir.exists())

    def test_invalid_platforms_json_fallback(self):
        dc = self.dc
        bad = self.tmp / "tools" / "bad_platforms.json"
        bad.write_text("{invalid json", encoding="utf-8")

        rules = dc.load_platform_rules(bad)
        # Should fall back to defaults containing 'quantconnect'
        self.assertIn("quantconnect", rules)
        self.assertTrue(rules["quantconnect"].flatten)

if __name__ == "__main__":
    unittest.main()
