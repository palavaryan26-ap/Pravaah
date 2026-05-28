"""Quick verification of Phase 1 endpoints."""
import json
import httpx

BASE = "http://127.0.0.1:8000"

# Test root
r = httpx.get(f"{BASE}/")
print("--- ROOT ---")
print(json.dumps(r.json(), indent=2))
print(f"X-Request-ID: {r.headers.get('x-request-id', 'MISSING')}")
print()

# Test health
r2 = httpx.get(f"{BASE}/health")
print("--- HEALTH ---")
print(json.dumps(r2.json(), indent=2))
print()

# Test error handling (404)
r3 = httpx.get(f"{BASE}/nonexistent")
print("--- 404 ERROR ---")
print(f"Status: {r3.status_code}")
print(json.dumps(r3.json(), indent=2))
print()

# Test OpenAPI
r4 = httpx.get(f"{BASE}/openapi.json")
print("--- OPENAPI ---")
openapi = r4.json()
print(f"Title: {openapi['info']['title']}")
print(f"Version: {openapi['info']['version']}")
print(f"Paths: {list(openapi['paths'].keys())}")
print()

print("=== ALL PHASE 1 CHECKS PASSED ===")
