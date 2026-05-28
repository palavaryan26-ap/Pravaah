"""Phase 6 verification - test the CLI end-to-end."""
import subprocess
import sys
import shutil
from pathlib import Path

PYTHON = sys.executable
CWD = str(Path(__file__).parent.parent)

print("=" * 60)
print("PHASE 6: CLI VERIFICATION")
print("=" * 60)
print()


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run a CLI command and return the result."""
    cmd = [PYTHON, "-m", "pravaah.cli.main", *args]
    return subprocess.run(
        cmd, capture_output=True, text=True, cwd=CWD, timeout=30,
    )


# 1. --help
print("[1] Testing --help ...")
r = run_cli("--help")
assert r.returncode == 0
assert "Pravaah CLI" in r.stdout
assert "run" in r.stdout
assert "info" in r.stdout
assert "list-plugins" in r.stdout
assert "list-models" in r.stdout
assert "list-hooks" in r.stdout
assert "routes" in r.stdout
assert "init-plugin" in r.stdout
print("    [PASS] Help shows all 7 commands")
print()

# 2. info
print("[2] Testing info ...")
r = run_cli("info")
assert r.returncode == 0
assert "Framework Info" in r.stdout
assert "Registry Summary" in r.stdout
assert "0.1.0" in r.stdout
print("    [PASS] Info displays framework + registry tables")
print()

# 3. list-plugins
print("[3] Testing list-plugins ...")
r = run_cli("list-plugins")
assert r.returncode == 0
assert "hello" in r.stdout
assert "notes" in r.stdout
assert "2 plugin(s) discovered" in r.stdout
print("    [PASS] Lists 2 plugins (hello, notes)")
print()

# 4. list-models
print("[4] Testing list-models ...")
r = run_cli("list-models")
assert r.returncode == 0
assert "Note" in r.stdout
assert "NoteCreate" in r.stdout
assert "NoteUpdate" in r.stdout
assert "NoteRead" in r.stdout
assert "1 model(s) registered" in r.stdout
print("    [PASS] Lists Note model with schemas")
print()

# 5. list-hooks
print("[5] Testing list-hooks ...")
r = run_cli("list-hooks")
assert r.returncode == 0
assert "after_create:Note" in r.stdout
assert "after_update:Note" in r.stdout
assert "after_delete:Note" in r.stdout
assert "3 hook(s)" in r.stdout
print("    [PASS] Lists 3 event hooks")
print()

# 6. routes
print("[6] Testing routes ...")
r = run_cli("routes")
assert r.returncode == 0
assert "/health" in r.stdout
assert "/ai/complete" in r.stdout
assert "/ai/summarize" in r.stdout
print("    [PASS] Lists API routes including health and AI endpoints")
print()

# 7. init-plugin
print("[7] Testing init-plugin ...")
plugin_path = Path(CWD) / "pravaah" / "plugins" / "test_scaffold"
if plugin_path.exists():
    shutil.rmtree(plugin_path)

r = run_cli("init-plugin", "test_scaffold")
assert r.returncode == 0
assert "Plugin scaffolded" in r.stdout
assert (plugin_path / "__init__.py").exists()
assert (plugin_path / "hooks.py").exists()

# Verify the scaffolded plugin is importable
r2 = subprocess.run(
    [PYTHON, "-c",
     "import pravaah.plugins.test_scaffold; "
     "print(pravaah.plugins.test_scaffold.TestScaffoldPlugin.manifest.name)"],
    capture_output=True, text=True, cwd=CWD, timeout=10,
)
assert r2.returncode == 0
assert "test_scaffold" in r2.stdout

# Cleanup
shutil.rmtree(plugin_path)
print("    [PASS] Scaffolds valid, importable plugin")
print()

# 8. init-plugin validation
print("[8] Testing init-plugin validation ...")
r = run_cli("init-plugin", "Invalid-Name!")
assert r.returncode == 1
print("    [PASS] Rejects invalid plugin names")
print()

# 9. run --help
print("[9] Testing run --help ...")
r = run_cli("run", "--help")
assert r.returncode == 0
assert "--host" in r.stdout
assert "--port" in r.stdout
assert "--reload" in r.stdout
assert "--workers" in r.stdout
print("    [PASS] Run command shows all options")
print()

print("=" * 60)
print("=== ALL PHASE 6 CHECKS PASSED (9/9) ===")
print("=" * 60)
