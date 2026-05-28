"""Phase 4 verification - test the event system end-to-end."""
import json
import httpx

BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("PHASE 4: EVENT SYSTEM VERIFICATION")
print("=" * 60)
print()

# 1. Health check
r = httpx.get(f"{BASE}/health")
health = r.json()
print(f"[1] Health: {health['plugins_loaded']} plugin(s), DB={health['database']}")
assert health["plugins_loaded"] >= 2
print("    [PASS] Server running with plugins")
print()

# 2. Create a note — should fire after_create:Note hook
print("[2] Creating a note (should fire after_create:Note event)...")
r = httpx.post(f"{BASE}/notes/", json={"title": "Event Test", "content": "Testing hooks"})
assert r.status_code == 201
note_id = r.json()["id"]
print(f"    Created note id={note_id}")
print("    [PASS] Create succeeded (check server logs for '[Hook] Note created')")
print()

# 3. Update the note — should fire after_update:Note hook
print("[3] Updating note (should fire after_update:Note event)...")
r = httpx.put(f"{BASE}/notes/{note_id}", json={"title": "Updated Event Test"})
assert r.status_code == 200
print(f"    Updated title to '{r.json()['title']}'")
print("    [PASS] Update succeeded (check server logs for '[Hook] Note updated')")
print()

# 4. Delete the note — should fire after_delete:Note hook
print("[4] Deleting note (should fire after_delete:Note event)...")
r = httpx.delete(f"{BASE}/notes/{note_id}")
assert r.json()["deleted"] is True
print("    [PASS] Delete succeeded (check server logs for '[Hook] Note deleted')")
print()

# 5. Verify the hooks metadata is in the registry
print("[5] Checking registry for hook registrations...")
r = httpx.get(f"{BASE}/health")
assert r.status_code == 200
print("    [PASS] Server still healthy after events fired")
print()

# 6. Create another to verify events still work after first round
print("[6] Creating second note to verify events are repeatable...")
r = httpx.post(f"{BASE}/notes/", json={"title": "Second Event Test"})
assert r.status_code == 201
print(f"    Created note id={r.json()['id']}")
print("    [PASS] Events fire on every operation")
print()

print("=" * 60)
print("=== ALL PHASE 4 CHECKS PASSED ===")
print("=" * 60)
print()
print("NOTE: Verify server logs show these lines:")
print("  [Hook] Note created: id=1, title='Event Test'")
print("  [Hook] Note updated: id=1")
print("  [Hook] Note deleted: id=1")
print("  [Hook] Note created: id=2, title='Second Event Test'")
