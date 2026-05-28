"""Phase 3 verification - test the CRUD engine end-to-end."""
import json
import httpx

BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("PHASE 3: CRUD ENGINE VERIFICATION")
print("=" * 60)
print()

# 1. Health check — should show 2 plugins
r = httpx.get(f"{BASE}/health")
health = r.json()
print(f"[1] Health: {health['plugins_loaded']} plugin(s), DB={health['database']}")
assert health["plugins_loaded"] >= 2
assert health["database"] == "connected"
print("    [PASS] Plugins loaded and DB connected")
print()

# 2. List notes (should be empty)
r = httpx.get(f"{BASE}/notes/")
data = r.json()
print(f"[2] List notes (empty): {json.dumps(data, indent=2)}")
assert data["total"] == 0
assert data["items"] == []
assert data["page"] == 1
print("    [PASS] Empty list with pagination metadata")
print()

# 3. Create a note
note1 = {"title": "First Note", "content": "Hello from CRUD engine!", "status": "active"}
r = httpx.post(f"{BASE}/notes/", json=note1)
created = r.json()
print(f"[3] Create note: status={r.status_code}")
print(f"    {json.dumps(created, indent=2)}")
assert r.status_code == 201
assert created["title"] == "First Note"
assert created["id"] is not None
note_id = created["id"]
print(f"    [PASS] Created with id={note_id}")
print()

# 4. Create a second note
note2 = {"title": "Second Note", "content": "Testing pagination"}
r = httpx.post(f"{BASE}/notes/", json=note2)
assert r.status_code == 201
note2_id = r.json()["id"]
print(f"[4] Created second note with id={note2_id}")
print("    [PASS]")
print()

# 5. Get note by ID
r = httpx.get(f"{BASE}/notes/{note_id}")
fetched = r.json()
print(f"[5] Get note {note_id}: {json.dumps(fetched, indent=2)}")
assert fetched["title"] == "First Note"
assert fetched["content"] == "Hello from CRUD engine!"
print("    [PASS] Read by ID works")
print()

# 6. List all notes (should have 2)
r = httpx.get(f"{BASE}/notes/")
data = r.json()
print(f"[6] List notes: total={data['total']}, pages={data['total_pages']}")
assert data["total"] == 2
assert len(data["items"]) == 2
print("    [PASS] Pagination metadata correct")
print()

# 7. Test pagination with page_size=1
r = httpx.get(f"{BASE}/notes/?page=1&page_size=1")
data = r.json()
print(f"[7] Paginated (page=1, size=1): {len(data['items'])} item, total_pages={data['total_pages']}")
assert len(data["items"]) == 1
assert data["total_pages"] == 2
r2 = httpx.get(f"{BASE}/notes/?page=2&page_size=1")
data2 = r2.json()
assert len(data2["items"]) == 1
print("    [PASS] Pagination with page_size=1 works")
print()

# 8. Update a note (partial)
r = httpx.put(f"{BASE}/notes/{note_id}", json={"title": "Updated Title"})
updated = r.json()
print(f"[8] Update note: {json.dumps(updated, indent=2)}")
assert updated["title"] == "Updated Title"
assert updated["content"] == "Hello from CRUD engine!"  # unchanged
print("    [PASS] Partial update works (only title changed)")
print()

# 9. Delete a note
r = httpx.delete(f"{BASE}/notes/{note_id}")
print(f"[9] Delete note: {r.json()}")
assert r.json()["deleted"] is True
print("    [PASS] Delete works")
print()

# 10. Verify deletion
r = httpx.get(f"{BASE}/notes/{note_id}")
print(f"[10] Get deleted note: status={r.status_code}")
assert r.status_code == 404
print("     [PASS] 404 after deletion")
print()

# 11. Verify remaining count
r = httpx.get(f"{BASE}/notes/")
assert r.json()["total"] == 1
print(f"[11] Remaining notes: {r.json()['total']}")
print("     [PASS] Count correct after deletion")
print()

# 12. OpenAPI has CRUD routes
r = httpx.get(f"{BASE}/openapi.json")
paths = list(r.json()["paths"].keys())
print(f"[12] OpenAPI paths: {paths}")
assert "/notes/" in paths
assert "/notes/{record_id}" in paths
print("     [PASS] CRUD routes in OpenAPI spec")
print()

# 13. Validation error (missing required field)
r = httpx.post(f"{BASE}/notes/", json={"content": "no title"})
print(f"[13] Validation error: status={r.status_code}")
assert r.status_code == 422
print("     [PASS] Validation rejects missing title")
print()

print("=" * 60)
print("=== ALL PHASE 3 CHECKS PASSED ===")
print("=" * 60)
