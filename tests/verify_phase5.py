"""Phase 5 verification - test the AI layer end-to-end."""
import json
import httpx

BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("PHASE 5: AI LAYER VERIFICATION")
print("=" * 60)
print()

# 1. Health check
r = httpx.get(f"{BASE}/health")
health = r.json()
print(f"[1] Health: {health['plugins_loaded']} plugin(s), DB={health['database']}")
assert health["status"] == "healthy"
print("    [PASS] Server healthy")
print()

# 2. AI Complete endpoint
print("[2] Testing POST /ai/complete ...")
r = httpx.post(f"{BASE}/ai/complete", json={
    "prompt": "What is Pravaah?",
    "temperature": 0.5,
})
print(f"    Status: {r.status_code}")
data = r.json()
print(f"    Response: {json.dumps(data, indent=2)}")
assert r.status_code == 200
assert data["content"]  # non-empty
assert data["model"]
assert "usage" in data
print("    [PASS] AI complete works")
print()

# 3. AI Summarize endpoint
print("[3] Testing POST /ai/summarize ...")
r = httpx.post(f"{BASE}/ai/summarize", json={
    "text": "Pravaah is a modern AI-native, plugin-driven backend framework "
            "focused on scalable enterprise application development through "
            "flow-oriented architecture. Everything flows.",
    "max_length": 50,
})
data = r.json()
print(f"    Status: {r.status_code}")
print(f"    Summary: {data.get('summary', '')[:100]}")
assert r.status_code == 200
assert data["summary"]
assert data["original_length"] > 0
print("    [PASS] AI summarize works")
print()

# 4. AI Extract endpoint
print("[4] Testing POST /ai/extract ...")
r = httpx.post(f"{BASE}/ai/extract", json={
    "text": "John Smith works at Acme Corp and his email is john@acme.com",
    "schema": {
        "name": "Person's full name",
        "company": "Company name",
        "email": "Email address",
    },
})
data = r.json()
print(f"    Status: {r.status_code}")
print(f"    Extracted: {json.dumps(data, indent=2)}")
assert r.status_code == 200
assert "data" in data
print("    [PASS] AI extract works")
print()

# 5. AI Classify endpoint
print("[5] Testing POST /ai/classify ...")
r = httpx.post(f"{BASE}/ai/classify", json={
    "text": "My order hasn't arrived yet and it's been 2 weeks!",
    "categories": ["billing", "shipping", "technical", "general"],
})
data = r.json()
print(f"    Status: {r.status_code}")
print(f"    Category: {data.get('category', '')}")
assert r.status_code == 200
assert data["category"]
print("    [PASS] AI classify works")
print()

# 6. AI Ask endpoint
print("[6] Testing POST /ai/ask ...")
r = httpx.post(f"{BASE}/ai/ask", json={
    "question": "What is the philosophy of Pravaah?",
    "context": "Pravaah is a backend framework. Its core philosophy is: Everything flows.",
})
data = r.json()
print(f"    Status: {r.status_code}")
print(f"    Answer: {data.get('answer', '')[:100]}")
assert r.status_code == 200
assert data["answer"]
print("    [PASS] AI ask works")
print()

# 7. AI routes in OpenAPI
print("[7] Checking AI routes in OpenAPI spec ...")
r = httpx.get(f"{BASE}/openapi.json")
paths = list(r.json()["paths"].keys())
ai_paths = [p for p in paths if p.startswith("/ai/")]
print(f"    AI paths: {ai_paths}")
assert "/ai/complete" in paths
assert "/ai/summarize" in paths
assert "/ai/extract" in paths
assert "/ai/classify" in paths
assert "/ai/ask" in paths
print("    [PASS] All 5 AI routes in OpenAPI")
print()

# 8. Validation error
print("[8] Testing validation (empty prompt) ...")
r = httpx.post(f"{BASE}/ai/complete", json={"prompt": ""})
print(f"    Status: {r.status_code}")
assert r.status_code == 422
print("    [PASS] Validation rejects empty prompt")
print()

print("=" * 60)
print("=== ALL PHASE 5 CHECKS PASSED ===")
print("=" * 60)
