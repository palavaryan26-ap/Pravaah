"""Phase 2 verification — test the plugin system end-to-end."""
import json
import httpx

BASE = "http://127.0.0.1:8000"

# Test health — should show 1 plugin loaded
r = httpx.get(f"{BASE}/health")
health = r.json()
print("--- HEALTH ---")
print(json.dumps(health, indent=2))
assert health["plugins_loaded"] >= 1, f"Expected >= 1 plugin, got {health['plugins_loaded']}"
print("[PASS] Plugin count in health check")
print()

# Test hello plugin endpoint
r2 = httpx.get(f"{BASE}/hello/")
print("--- HELLO PLUGIN ---")
print(json.dumps(r2.json(), indent=2))
assert r2.status_code == 200, f"Expected 200, got {r2.status_code}"
assert r2.json()["plugin"] == "hello"
print("[PASS] Hello plugin endpoint works")
print()

# Test plugin manifest endpoint
r3 = httpx.get(f"{BASE}/hello/manifest")
print("--- PLUGIN MANIFEST ---")
print(json.dumps(r3.json(), indent=2))
assert r3.json()["name"] == "hello"
assert r3.json()["enabled"] is True
print("[PASS] Manifest endpoint works")
print()

# Test OpenAPI includes plugin routes
r4 = httpx.get(f"{BASE}/openapi.json")
paths = list(r4.json()["paths"].keys())
print("--- OPENAPI PATHS ---")
print(paths)
assert "/hello/" in paths, f"/hello/ not in {paths}"
assert "/hello/manifest" in paths, f"/hello/manifest not in {paths}"
print("[PASS] Plugin routes in OpenAPI spec")
print()

# Test root still works
r5 = httpx.get(f"{BASE}/")
print("--- ROOT ---")
print(json.dumps(r5.json(), indent=2))
print("[PASS] Root endpoint unaffected")
print()

print("=== ALL PHASE 2 CHECKS PASSED ===")
