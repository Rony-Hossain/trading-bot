# deploy_core.py — stdlib-only multi-platform build core (dist/<platform> output)

from __future__ import annotations

import ast
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# --------------------------- Platform Rules ---------------------------

@dataclass
class PlatformRules:
    name: str
    flatten: bool = True
    max_file_size: Optional[int] = None
    generate_upload_order: bool = False
    bundle_single_file: bool = False
    char_restrictions: List[str] = field(default_factory=list)
    file_order_priority: List[str] = field(default_factory=list)
    supports_packages: bool = True
    # NOTE: output_dir_name retained for compatibility; actual output is dist/<platform>
    output_dir_name: str = "build"
    # Hooks
    pre_build_script: Optional[str] = None
    post_build_script: Optional[str] = None
    pre_build_args: List[str] = field(default_factory=list)
    post_build_args: List[str] = field(default_factory=list)
    hook_timeout_sec: Optional[int] = 300  # None => no timeout

    def validate_content(self, content: str, filename: str) -> Tuple[bool, List[str]]:
        warns = []
        if self.max_file_size and len(content) > self.max_file_size:
            warns.append(f"{filename}: Exceeds max size ({len(content)} > {self.max_file_size})")
        for pattern in self.char_restrictions:
            try:
                if re.search(pattern, content):
                    m = re.findall(pattern, content)
                    preview = ", ".join(map(str, m[:5]))
                    warns.append(f"{filename}: Contains invalid characters: {preview}")
            except re.error as e:
                warns.append(f"{filename}: Invalid regex '{pattern}': {e}")
        return len(warns) == 0, warns

    @classmethod
    def _expect_type(cls, val: Any, typ, field: str):
        if val is None:
            return
        if not isinstance(val, typ):
            raise ValueError(f"Invalid type for '{field}': expected {typ.__name__}, got {type(val).__name__}")

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlatformRules":
        if not isinstance(d.get("name"), str):
            raise ValueError("Missing or invalid 'name' in platform spec")
        cls._expect_type(d.get("flatten", True), bool, "flatten")
        if d.get("max_file_size", None) is not None and not isinstance(d.get("max_file_size"), int):
            raise ValueError("'max_file_size' must be int or null")
        cls._expect_type(d.get("generate_upload_order", False), bool, "generate_upload_order")
        cls._expect_type(d.get("bundle_single_file", False), bool, "bundle_single_file")
        if d.get("char_restrictions") is not None and not isinstance(d.get("char_restrictions"), list):
            raise ValueError("'char_restrictions' must be a list")
        if d.get("file_order_priority") is not None and not isinstance(d.get("file_order_priority"), list):
            raise ValueError("'file_order_priority' must be a list")
        cls._expect_type(d.get("supports_packages", True), bool, "supports_packages")
        if not isinstance(d.get("output_dir_name", "build"), str):
            raise ValueError("'output_dir_name' must be a string")
        for key in ("pre_build_script", "post_build_script"):
            if d.get(key) is not None and not isinstance(d.get(key), str):
                raise ValueError(f"'{key}' must be a string path")
        for key in ("pre_build_args", "post_build_args"):
            if d.get(key) is not None and not isinstance(d.get(key), list):
                raise ValueError(f"'{key}' must be a list")
        if d.get("hook_timeout_sec", None) is not None and not isinstance(d.get("hook_timeout_sec"), int):
            raise ValueError("'hook_timeout_sec' must be int or null")
        return cls(
            name=d["name"],
            flatten=bool(d.get("flatten", True)),
            max_file_size=d.get("max_file_size", None),
            generate_upload_order=bool(d.get("generate_upload_order", False)),
            bundle_single_file=bool(d.get("bundle_single_file", False)),
            char_restrictions=list(d.get("char_restrictions", [])),
            file_order_priority=list(d.get("file_order_priority", [])),
            supports_packages=bool(d.get("supports_packages", True)),
            output_dir_name=str(d.get("output_dir_name", "build")),
            pre_build_script=d.get("pre_build_script"),
            post_build_script=d.get("post_build_script"),
            pre_build_args=list(d.get("pre_build_args", [])),
            post_build_args=list(d.get("post_build_args", [])),
            hook_timeout_sec=d.get("hook_timeout_sec", 300),
        )


def _default_rules() -> Dict[str, PlatformRules]:
    return {
        "quantconnect": PlatformRules(
            name="QuantConnect",
            flatten=True,
            max_file_size=32000,
            generate_upload_order=True,
            bundle_single_file=False,
            char_restrictions=[r'[\U0001F300-\U0001FAFF]'],
            file_order_priority=["main.py", "config.py"],
            supports_packages=False,
            output_dir_name="quantconnect",
        ),
        "backtrader": PlatformRules(
            name="Backtrader",
            flatten=False,
            supports_packages=True,
            output_dir_name="backtrader_build",
        ),
        "zipline": PlatformRules(
            name="Zipline",
            flatten=False,
            supports_packages=True,
            output_dir_name="zipline_build",
        ),
        "freqtrade": PlatformRules(
            name="Freqtrade",
            flatten=False,
            supports_packages=True,
            output_dir_name="freqtrade_build",
        ),
    }


def load_platform_rules(config_path: Optional[Path]) -> Dict[str, PlatformRules]:
    resolved: Optional[Path] = None
    if config_path is not None:
        resolved = Path(config_path)
    else:
        envp = os.environ.get("PLATFORM_RULES_PATH")
        if envp:
            resolved = Path(envp)
        else:
            here = Path(__file__).resolve().parent
            cand = here / "platforms.json"
            if cand.exists():
                resolved = cand
            else:
                root = Path(__file__).resolve().parents[1]
                cand = root / "tools" / "platforms.json"
                resolved = cand if cand.exists() else None

    if resolved and resolved.exists():
        try:
            data = json.loads(resolved.read_text(encoding="utf-8"))
            plat = data.get("platforms", {})
            rules: Dict[str, PlatformRules] = {}
            for k, spec in plat.items():
                try:
                    rules[k] = PlatformRules.from_dict(spec)
                except Exception as ve:
                    print(f"[platforms.json] Skipping '{k}': {ve}", file=sys.stderr)
            if rules:
                return rules
            print("[platforms.json] No valid platforms found; using defaults.", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"[platforms.json] JSON decode error: {e} — using defaults.", file=sys.stderr)
        except Exception as e:
            print(f"[platforms.json] Failed to load: {e} — using defaults.", file=sys.stderr)

    return _default_rules()


def effective_rules(config_path: Optional[Path]) -> Dict[str, Dict[str, Any]]:
    return {k: vars(v) for k, v in load_platform_rules(config_path).items()}

# ---------------------- Component Discovery ----------------------

@dataclass
class Component:
    name: str
    source: Path
    category: str
    required: bool = False
    description: str = ""
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "source": str(self.source),
            "category": self.category, "required": self.required,
            "description": self.description
        }

class ComponentDiscovery:
    CATEGORY_PATTERNS = {
        "CORE":      ["main", "config", "universe"],
        "STRATEGY":  ["strategy", "signal", "extreme", "hmm", "regime", "avwap", "indicator", "alpha"],
        "RISK":      ["risk", "position", "portfolio", "drawdown", "cvar", "var"],
        "INFRA":     ["logger", "log", "alert", "monitor", "util", "helper", "health"],
        "DATA":      ["data", "feed", "loader", "provider"],
        "EXECUTION": ["executor", "order", "trade", "broker", "fill"],
        "ANALYSIS":  ["analyzer", "backtest", "performance", "metric", "report"],
    }
    FIXED_CORES = ["src/main.py", "config/config.py"]

    @classmethod
    def _infer_category(cls, filename: str) -> str:
        s = filename.lower()
        for cat, keys in cls.CATEGORY_PATTERNS.items():
            if any(k in s for k in keys):
                return cat
        return "OTHER"

    @classmethod
    def discover_components(cls, root_dir: Path,
                            include_patterns: Optional[List[str]] = None,
                            exclude_patterns: Optional[List[str]] = None) -> Dict[str, Component]:
        comps: Dict[str, Component] = {}
        include_patterns = include_patterns or ["src/components/*.py", "src/**/*.py"]
        exclude_patterns = exclude_patterns or ["*test*.py", "*__pycache__*", "*__init__.py"]

        for core in cls.FIXED_CORES:
            p = root_dir / core
            if p.exists():
                comps[p.stem] = Component(p.stem, Path(core), "CORE", True, f"Core component: {p.stem}")

        for pat in include_patterns:
            for fp in root_dir.glob(pat):
                if not fp.is_file():
                    continue
                rel = fp.relative_to(root_dir)
                if str(rel).replace("\\", "/") in cls.FIXED_CORES:
                    continue
                if any(fp.match(ex) for ex in exclude_patterns):
                    continue
                name = fp.stem
                comps[name] = Component(name, rel, cls._infer_category(name), False, "Auto-discovered component")
        return comps

def discover_and_list_components(root_dir: Path,
                                 include_patterns: Optional[List[str]] = None,
                                 exclude_patterns: Optional[List[str]] = None) -> Dict[str, Component]:
    return ComponentDiscovery.discover_components(root_dir, include_patterns, exclude_patterns)

def list_components(root_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    root_dir = root_dir or Path(__file__).resolve().parents[1]
    return {k: v.to_dict() for k, v in discover_and_list_components(root_dir).items()}

# --------------------------- AST Optimizer ---------------------------

class ASTOptimizer:
    @staticmethod
    def minify_code(source: str, remove_docstrings: bool = True) -> str:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source
        if remove_docstrings:
            for n in ast.walk(tree):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                    if n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str):
                        n.body.pop(0)
        try:
            txt = ast.unparse(tree)
        except Exception:
            return source
        lines = [ln.rstrip() for ln in txt.splitlines() if ln.strip()]
        return "\n".join(lines)

    @staticmethod
    def tree_shake(source: str, entry_points: Optional[Set[str]] = None) -> str:
        entry_points = entry_points or {"Initialize", "OnData", "main"}
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source

        definitions: Dict[str, ast.AST] = {}
        uses: Dict[str, Set[str]] = defaultdict(set)

        class DefV(ast.NodeVisitor):
            def visit_FunctionDef(self, n):
                if n.col_offset == 0: definitions[n.name] = n
                self.generic_visit(n)
            def visit_AsyncFunctionDef(self, n):
                if n.col_offset == 0: definitions[n.name] = n
                self.generic_visit(n)
            def visit_ClassDef(self, n):
                if n.col_offset == 0: definitions[n.name] = n
                self.generic_visit(n)
            def visit_Assign(self, n):
                if n.col_offset == 0:
                    for t in n.targets:
                        if isinstance(t, ast.Name): definitions[t.id] = n
                self.generic_visit(n)

        class UseV(ast.NodeVisitor):
            def __init__(self, cur: str): self.cur = cur
            def visit_Name(self, n):
                if isinstance(n.ctx, ast.Load): uses[self.cur].add(n.id)
            def visit_Attribute(self, n):
                if isinstance(n.value, ast.Name): uses[self.cur].add(n.value.id)
                self.generic_visit(n)
            def visit_Global(self, n):
                for nm in n.names: uses[self.cur].add(nm)

        DefV().visit(tree)
        for nm, node in definitions.items():
            UseV(nm).visit(node)

        reachable: Set[str] = set()
        q: List[str] = list(entry_points)
        while q:
            cur = q.pop(0)
            if cur in reachable:
                continue
            reachable.add(cur)
            for used in uses.get(cur, set()):
                if used in definitions and used not in reachable:
                    q.append(used)

        new_body: List[ast.stmt] = []
        for node in tree.body:
            keep = True
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                keep = node.name in reachable or node.name in entry_points
            elif isinstance(node, ast.Assign):
                keep = any(isinstance(t, ast.Name) and (t.id in reachable or t.id in entry_points) for t in node.targets)
            if keep:
                new_body.append(node)
        tree.body = new_body
        try:
            return ast.unparse(tree)
        except Exception:
            return source

    @staticmethod
    def split_file(source: str, max_size: int, base_filename: str) -> List[Tuple[str, str]]:
        if len(source) <= max_size:
            return [(f"{base_filename}.py", source)]
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return [(f"{base_filename}.py", source)]

        imports, defs = [], []
        for n in tree.body:
            (imports if isinstance(n, (ast.Import, ast.ImportFrom)) else defs).append(n)

        try:
            import_block = ast.unparse(ast.Module(body=imports, type_ignores=[]))
        except Exception:
            import_block = ""
        import_sz = len(import_block) + 2

        parts: List[List[ast.stmt]] = []
        cur, cur_sz = [], import_sz
        for n in defs:
            try:
                txt = ast.unparse(n)
                nsz = len(txt)
            except Exception:
                nsz = 200
            if cur and cur_sz + nsz > max_size:
                parts.append(cur); cur = [n]; cur_sz = import_sz + nsz
            else:
                cur.append(n); cur_sz += nsz
        if cur:
            parts.append(cur)

        out: List[Tuple[str, str]] = []
        for i, body in enumerate(parts, 1):
            mod = ast.Module(body=imports + body, type_ignores=[])
            try:
                code = ast.unparse(mod)
            except Exception:
                try:
                    code = (import_block + "\n\n" + "\n\n".join(ast.unparse(b) for b in body))
                except Exception:
                    return [(f"{base_filename}.py", source)]
            out.append((f"{base_filename}_part{i}.py", code))
        return out or [(f"{base_filename}.py", source)]

# ------------- Optional coverage-assisted shaking (opt-in) -------------

def _coverage_available() -> bool:
    from shutil import which
    return which("coverage") is not None

def _try_run_coverage(root: Path, cmd: str, stats: "BuildStats") -> Optional[Dict[str, Any]]:
    if not _coverage_available():
        stats.warnings.append("coverage-assisted shake requested, but 'coverage' is not installed. Hint: pip install coverage")
        return None
    try:
        subprocess.run(["coverage", "erase"], cwd=str(root), check=False,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p = subprocess.run(["coverage", "run", "-m"] + cmd.split(), cwd=str(root),
                           check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stats.hooks.append({"phase": "coverage-run", "script": cmd, "returncode": p.returncode,
                            "stdout": p.stdout, "stderr": p.stderr})
        pj = subprocess.run(["coverage", "json", "-o", "coverage.json"], cwd=str(root),
                            check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stats.hooks.append({"phase": "coverage-json", "script": "coverage json", "returncode": pj.returncode,
                            "stdout": pj.stdout, "stderr": pj.stderr})
        cov_path = root / "coverage.json"
        if not cov_path.exists():
            stats.warnings.append("coverage.json not produced; skipping coverage-assisted shaking.")
            return None
        return json.loads(cov_path.read_text(encoding="utf-8"))
    except Exception as e:
        stats.warnings.append(f"coverage-assisted shake failed: {e}")
        return None

def _prune_with_coverage(source: str, executed_lines: Set[int]) -> str:
    if not executed_lines:
        return source
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    def span_used(n: ast.AST) -> bool:
        ln = getattr(n, "lineno", None)
        end = getattr(n, "end_lineno", ln)
        if ln is None:
            return True
        for k in range(ln, (end or ln) + 1):
            if k in executed_lines:
                return True
        return False

    new_body: List[ast.stmt] = []
    for node in tree.body:
        keep = True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign)):
            keep = span_used(node)
        if keep:
            new_body.append(node)
    tree.body = new_body
    try:
        return ast.unparse(tree)
    except Exception:
        return source

# --------------------------- Build Stats ---------------------------

class BuildStats:
    def __init__(self):
        self.original_size = 0
        self.final_size = 0
        self.files_processed = 0
        self.files_split = 0
        self.files_bundled = 0
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.per_file_stats: List[Dict[str, Any]] = []
        self.hooks: List[Dict[str, Any]] = []

    def add_file(self, path: str, original_size: int, final_size: int, split: bool = False):
        self.original_size += original_size
        self.final_size += final_size
        self.files_processed += 1
        if split:
            self.files_split += 1
        reduction = 0.0
        if original_size:
            reduction = round((1 - (final_size / original_size)) * 100, 2)
        self.per_file_stats.append({
            "path": path,
            "original_bytes": original_size,
            "final_bytes": final_size,
            "reduction_percent": reduction,
            "split": split
        })

    def summary(self) -> Dict[str, Any]:
        reduction = (1 - self.final_size / self.original_size) * 100 if self.original_size else 0.0
        return {
            "original_size_bytes": self.original_size,
            "final_size_bytes": self.final_size,
            "size_reduction_percent": round(reduction, 2),
            "files_processed": self.files_processed,
            "files_split": self.files_split,
            "files_bundled": self.files_bundled,
            "warnings": self.warnings,
            "errors": self.errors,
            "per_file_stats": self.per_file_stats,
            "hooks": self.hooks
        }

# --------------------------- Helpers ---------------------------

def _write_text(path: Path, content: str, stats: BuildStats):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        stats.errors.append(f"Failed to write {path}: {e}")

def _run_hook(script_path: Path, cwd: Path, stats: BuildStats, phase: str,
              args_list: Optional[List[str]], timeout_sec: Optional[int]):
    try:
        if not script_path.exists():
            stats.warnings.append(f"{phase} hook not found: {script_path}")
            return
        cmd = [sys.executable, str(script_path)] + (args_list or [])
        p = subprocess.run(cmd, cwd=str(cwd), timeout=timeout_sec,
                           check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stats.hooks.append({
            "phase": phase, "script": str(script_path), "args": args_list or [],
            "timeout_sec": timeout_sec, "returncode": p.returncode,
            "stdout": p.stdout, "stderr": p.stderr
        })
        if p.returncode != 0:
            stats.warnings.append(f"{phase} hook returned non-zero exit: {p.returncode}")
    except subprocess.TimeoutExpired:
        stats.errors.append(f"{phase} hook timed out: {script_path} (timeout={timeout_sec}s)")
    except Exception as e:
        stats.errors.append(f"{phase} hook failed ({script_path}): {e}")

def _make_facade_for_parts(target_dir: Path, original_filename: str,
                           part_files: List[str], stats: BuildStats, dry_run: bool):
    lines = [f"# Auto-generated facade for split file: {original_filename}"]
    for pf in part_files:
        lines.append(f"from {Path(pf).stem} import *")
    facade = "\n".join(lines) + "\n"
    dest = target_dir / original_filename
    if not dry_run:
        _write_text(dest, facade, stats)
        if not dest.exists():
            stats.warnings.append(f"Split facade could not be created: {dest}")

# --------------------------- Cache helpers ---------------------------

def _cache_total_bytes(cache_dir: Path) -> int:
    total = 0
    for f in cache_dir.glob("*"):
        try:
            total += f.stat().st_size
        except Exception:
            pass
    return total

def _cache_prune_to_limit(cache_dir: Path, max_bytes: int):
    files = [f for f in cache_dir.glob("*") if f.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime)
    total = _cache_total_bytes(cache_dir)
    idx = 0
    while total > max_bytes and idx < len(files):
        try:
            sz = files[idx].stat().st_size
            files[idx].unlink(missing_ok=True)
            total -= sz
        except Exception:
            pass
        idx += 1

# --------------------------- Build Core ---------------------------

def clean_build(root_dir: Path, platform: str = "quantconnect",
                platform_rules: Optional[Dict[str, PlatformRules]] = None,
                cache_clean: bool = False,
                cache_dir: Optional[Path] = None) -> bool:
    """
    Remove dist/<platform> and (optionally) the transform cache.
    """
    _ = platform_rules or load_platform_rules(None)
    target = Path(root_dir) / "dist" / platform
    removed = False
    if target.exists() and target.is_dir():
        shutil.rmtree(target)
        removed = True
    if cache_clean:
        cdir = cache_dir or (Path(root_dir) / ".build_cache")
        shutil.rmtree(cdir, ignore_errors=True)
    return removed

clean_quantconnect = clean_build

def build_for_platform(
    root_dir: Path,
    platform: str = "quantconnect",
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    dry_run: bool = False,
    force: bool = False,
    minify: bool = False,
    bundle: bool = False,
    tree_shake: bool = False,
    platform_config: Optional[Path] = None,
    verbose: bool = False,
    # bundle controls
    bundle_name: str = "strategy.py",
    shake_with_coverage_cmd: Optional[str] = None,
    entry_points: Optional[Set[str]] = None,
    # cache
    use_cache: bool = False,
    cache_dir: Optional[Path] = None,
    cache_max_bytes: Optional[int] = None,
    cache_clean: bool = False,
    # logs
    log_max_chars: Optional[int] = 500,
    # NEW: hook arg overrides + strict entry validation
    pre_args_override: Optional[List[str]] = None,
    post_args_override: Optional[List[str]] = None,
    shake_strict: bool = False,
) -> Dict[str, Any]:
    """
    Build deployment package for the given platform into dist/<platform>/.
    """
    rules_map = load_platform_rules(platform_config) if platform_config else load_platform_rules(None)
    root_dir = Path(root_dir)
    include, exclude = include or [], exclude or []

    rules = rules_map.get(platform)
    if not rules:
        return {"success": False, "error": f"Unknown platform: {platform}",
                "available_platforms": list(rules_map.keys())}

    # ---- OUTPUT TARGET: dist/<platform> ----
    target = root_dir / "dist" / platform

    timestamp = datetime.utcnow().isoformat() + "Z"
    stats = BuildStats()
    copied: List[str] = []
    skipped: List[str] = []

    # Hooks: pre-build (allow CLI override of args)
    if rules.pre_build_script and not dry_run:
        _run_hook(
            (root_dir / rules.pre_build_script) if not Path(rules.pre_build_script).is_absolute()
            else Path(rules.pre_build_script),
            cwd=root_dir, stats=stats, phase="pre-build",
            args_list=(pre_args_override if pre_args_override is not None else rules.pre_build_args),
            timeout_sec=rules.hook_timeout_sec
        )

    # Prepare outdir
    if target.exists():
        if not force:
            return {
                "root": str(target), "platform": platform, "timestamp": timestamp,
                "dry_run": dry_run, "success": False,
                "error": f"{(Path('dist') / platform)}/ already exists; use --force",
                "copied": [], "skipped": [], "stats": stats.summary(),
                "optimizations": {"minify": minify, "bundle": bundle, "tree_shake": tree_shake,
                                  "bundle_name": bundle_name,
                                  "shake_with_coverage_cmd": shake_with_coverage_cmd}
            }
        if not dry_run:
            shutil.rmtree(target)
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    # coverage lines map
    coverage_map: Dict[str, Set[int]] = {}
    if shake_with_coverage_cmd:
        cov_json = _try_run_coverage(root_dir, shake_with_coverage_cmd, stats)
        if cov_json and "files" in cov_json:
            for fpath, meta in cov_json["files"].items():
                try:
                    executed = set(meta.get("executed_lines", []))
                    coverage_map[Path(fpath).resolve().as_posix()] = executed
                except Exception:
                    continue

    components = discover_and_list_components(root_dir)

    # Verbose summary to stderr
    if verbose:
        counts = Counter(c.category for c in components.values())
        req = [n for n, c in components.items() if c.required]
        print("[discovery] categories:", ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())), file=sys.stderr)
        print("[discovery] required:", ", ".join(sorted(req)) or "<none>", file=sys.stderr)

    # Select
    selected: List[str] = [n for n, c in components.items() if c.required]
    for n in include:
        if n in components and n not in selected:
            selected.append(n)
    selected = [n for n in selected if n not in exclude]

    def sort_key(n: str):
        filename = components[n].source.name
        if filename in rules.file_order_priority:
            return (0, rules.file_order_priority.index(filename))
        return (1, filename.lower())
    selected.sort(key=sort_key)

    # Validate entry points exist somewhere if provided
    if entry_points:
        defined_names: Set[str] = set()
        for comp_name in selected:
            srcp = root_dir / components[comp_name].source
            try:
                txt = srcp.read_text(encoding="utf-8")
                tree = ast.parse(txt)
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        defined_names.add(node.name)
                    elif isinstance(node, ast.Assign):
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                defined_names.add(t.id)
            except Exception:
                pass
        unknown = [e for e in entry_points if e not in defined_names]
        if unknown:
            msg = f"Entry points not found in selected sources: {', '.join(sorted(unknown))}"
            if shake_strict:
                # treat as build error
                stats.errors.append(msg)
            else:
                stats.warnings.append(msg)

    # Cache init/cleanup
    cache_dir = (root_dir / ".build_cache") if (use_cache and cache_dir is None) else cache_dir
    if use_cache and cache_dir:
        if cache_clean:
            shutil.rmtree(cache_dir, ignore_errors=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        if cache_max_bytes and cache_max_bytes > 0:
            _cache_prune_to_limit(cache_dir, cache_max_bytes)

    # Bundle accumulators
    bundle_imports: List[str] = []
    bundle_bodies: List[str] = []
    bundle_exports: Set[str] = set()

    # Process files
    for name in selected:
        comp = components.get(name)
        if not comp:
            skipped.append(name); stats.warnings.append(f"Unknown component: {name}"); continue
        src = root_dir / comp.source
        if not src.exists():
            skipped.append(str(comp.source)); stats.warnings.append(f"Source not found: {comp.source}"); continue

        try:
            content = src.read_text(encoding="utf-8")
        except Exception as e:
            stats.errors.append(f"Failed to read {src}: {e}"); continue

        # cache key
        transformed = None
        cache_key = None
        if use_cache and cache_dir:
            key_seed = f"{src}:{len(content)}:{int(minify)}:{int(tree_shake)}:{sorted(list(entry_points or set()))}:{bool(shake_with_coverage_cmd)}"
            cache_key = hashlib.sha256(key_seed.encode("utf-8")).hexdigest()
            cache_file = cache_dir / f"{src.stem}_{cache_key}.py"
            if cache_file.exists():
                try:
                    transformed = cache_file.read_text(encoding="utf-8")
                except Exception:
                    transformed = None

        orig_len = len(content)
        if transformed is None:
            transformed = content
            if minify:
                transformed = ASTOptimizer.minify_code(transformed)
            if tree_shake:
                transformed = ASTOptimizer.tree_shake(transformed, entry_points=entry_points or None)
            if shake_with_coverage_cmd and coverage_map:
                executed = coverage_map.get(src.resolve().as_posix(), set())
                if executed:
                    transformed = _prune_with_coverage(transformed, executed)
                else:
                    stats.warnings.append(f"Coverage shows no executed lines for {comp.source}; kept as-is.")
            if use_cache and cache_dir and cache_key:
                try:
                    (cache_dir / f"{src.stem}_{cache_key}.py").write_text(transformed, encoding="utf-8")
                except Exception:
                    pass

        # validate
        _, warns = rules.validate_content(transformed, comp.source.name)
        stats.warnings.extend(warns)

        # Bundle path
        if bundle and rules.bundle_single_file:
            try:
                tree = ast.parse(transformed)
                for node in tree.body:
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        bundle_imports.append(ast.unparse(node))
                    else:
                        bundle_bodies.append(ast.unparse(node))
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            bundle_exports.add(node.name)
                        elif isinstance(node, ast.Assign):
                            for t in node.targets:
                                if isinstance(t, ast.Name):
                                    bundle_exports.add(t.id)
            except SyntaxError:
                bundle_bodies.append(transformed)
            stats.add_file(str(comp.source), orig_len, len(transformed))
            continue

        # Size splitting
        part_files_written: List[str] = []
        if rules.max_file_size and len(transformed) > rules.max_file_size:
            parts = ASTOptimizer.split_file(transformed, rules.max_file_size, src.stem)
            stats.files_split += 1
            for part_filename, part_content in parts:
                _, part_warns = rules.validate_content(part_content, part_filename)
                stats.warnings.extend(part_warns)
                dest = (target / part_filename) if rules.flatten else (target / comp.source.parent / part_filename)
                if dry_run:
                    copied.append(str(dest))
                else:
                    _write_text(dest, part_content, stats)
                    copied.append(str(dest))
                part_files_written.append(dest.name)
                stats.add_file(str(dest), 0, len(part_content), split=True)
            # Facade
            facade_dir = target if rules.flatten else (target / comp.source.parent)
            dest = (facade_dir / src.name)
            if dry_run:
                copied.append(str(dest))
            else:
                _make_facade_for_parts(facade_dir, src.name, part_files_written, stats, dry_run)
                copied.append(str(dest))
        else:
            dest = (target / src.name) if rules.flatten else (target / comp.source)
            if dry_run:
                copied.append(str(dest))
            else:
                _write_text(dest, transformed, stats)
            copied.append(str(dest))
            stats.add_file(str(dest), orig_len, len(transformed))

    # Emit bundle if requested
    if bundle and rules.bundle_single_file and (bundle_bodies or bundle_imports):
        # sanitize bundle name (no path traversal; invalid chars -> "_")
        bn = Path(bundle_name).name
        bn = re.sub(r'[\\/:*?"<>|]', "_", bn)
        # enforce valid suffix (.py or .py.gz)
        if bn.endswith(".gz") and not bn.endswith(".py.gz"):
            bn = bn.replace(".gz", ".py.gz")
        if not (bn.endswith(".py") or bn.endswith(".py.gz")):
            bn += ".py"

        all_imports = "\n".join(sorted(set(bundle_imports)))
        all_body = "\n\n".join(bundle_bodies)
        exports_block = ""
        if bundle_exports:
            exports_block = "\n__all__ = " + repr(sorted(bundle_exports)) + "\n"
        bundled = (all_imports + "\n\n" + all_body + exports_block).strip() + "\n"

        bundle_path = target / bn
        if bundle_path.suffix == ".gz":
            if not dry_run:
                try:
                    with gzip.open(bundle_path, "wt", encoding="utf-8") as f:
                        f.write(bundled)
                except Exception as e:
                    stats.errors.append(f"Failed to write compressed bundle: {e}")
            copied.append(str(bundle_path))
            # NEW: helpful note about compressed bundle
            stats.warnings.append(f"Bundle written as compressed file '{bundle_path.name}'. "
                                  f"Unzip to a .py if the platform cannot load .py.gz.")
        else:
            if not dry_run:
                _write_text(bundle_path, bundled, stats)
            copied.append(str(bundle_path))
        stats.files_bundled = 1

    # UPLOAD_ORDER
    if rules.generate_upload_order and not dry_run:
        order = target / "UPLOAD_ORDER.txt"
        try:
            with order.open("w", encoding="utf-8") as f:
                for n in selected:
                    comp = components.get(n)
                    if comp:
                        f.write(f"{Path(comp.source).name}\n")
        except Exception as e:
            stats.warnings.append(f"Failed to write UPLOAD_ORDER.txt: {e}")

    # Hooks: post-build (allow CLI override of args)
    if rules.post_build_script and not dry_run:
        _run_hook(
            (root_dir / rules.post_build_script) if not Path(rules.post_build_script).is_absolute()
            else Path(rules.post_build_script),
            cwd=root_dir, stats=stats, phase="post-build",
            args_list=(post_args_override if post_args_override is not None else rules.post_build_args),
            timeout_sec=rules.hook_timeout_sec
        )

    success = not stats.errors

    # Optionally trim logs here; CLI may request full detail by passing None
    if log_max_chars is not None and log_max_chars > 0:
        for h in stats.hooks:
            if "stdout" in h and h["stdout"]:
                h["stdout"] = h["stdout"][:log_max_chars]
            if "stderr" in h and h["stderr"]:
                h["stderr"] = h["stderr"][:log_max_chars]

    return {
        "root": str(target), "platform": platform, "timestamp": timestamp,
        "dry_run": dry_run, "success": success, "copied": copied, "skipped": skipped,
        "stats": stats.summary(),
        "optimizations": {
            "minify": minify, "bundle": bundle, "tree_shake": tree_shake,
            "bundle_name": Path(bundle_name).name,
            "shake_with_coverage_cmd": shake_with_coverage_cmd,
            "entry_points": sorted(list(entry_points or set())),
            "use_cache": use_cache,
            "cache_dir": str(cache_dir) if cache_dir else None,
            "cache_max_bytes": cache_max_bytes,
            "shake_strict": shake_strict,
        }
    }

def build_quantconnect(root_dir: Path,
                       include: Optional[List[str]] = None,
                       exclude: Optional[List[str]] = None,
                       dry_run: bool = True,
                       force: bool = False,
                       platform_config: Optional[Path] = None) -> Dict[str, Any]:
    res = build_for_platform(root_dir=root_dir, platform="quantconnect", include=include, exclude=exclude,
                             dry_run=dry_run, force=force, minify=False, bundle=False, tree_shake=False,
                             platform_config=platform_config)
    merged = res["stats"]["warnings"] + res["stats"]["errors"]
    return {"root": res["root"], "timestamp": res["timestamp"], "dry_run": res["dry_run"],
            "success": res["success"], "copied": res["copied"], "skipped": res["skipped"],
            "warnings": merged}
