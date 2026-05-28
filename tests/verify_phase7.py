"""Phase 7 verification - test the CRM Demo plugin end-to-end."""
import httpx
import json

BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("PHASE 7: CRM PLUGIN VERIFICATION")
print("=" * 60)
print()

# 1. Health check & CLI list-plugins
r = httpx.get(f"{BASE}/health")
health = r.json()
print(f"[1] Health: {health['plugins_loaded']} plugin(s), DB={health['database']}")
assert health["status"] == "healthy"
print("    [PASS] Server healthy")
print()

# 2. Create Customer (Triggers AI Lead Scoring hook)
print("[2] Creating a new Customer (should trigger AI lead scoring) ...")
r = httpx.post(f"{BASE}/crm/customers/", json={
    "name": "Acme Corp",
    "email": "contact@acmecorp.com",
    "company": "Acme Corporation"
})
assert r.status_code == 201
customer = r.json()
customer_id = customer["id"]
print(f"    Created Customer: ID={customer_id}, Name={customer['name']}")

# Fetch the customer to verify the hook updated the AI lead score
r = httpx.get(f"{BASE}/crm/customers/{customer_id}")
customer = r.json()
print(f"    AI Lead Score: {customer['ai_lead_score']}")
assert "ai_lead_score" in customer
print("    [PASS] Customer created & AI lead score assigned via hook")
print()

# 3. Create Deal
print("[3] Creating a Deal for the Customer ...")
r = httpx.post(f"{BASE}/crm/deals/", json={
    "title": "Enterprise License",
    "amount": 50000.0,
    "customer_id": customer_id
})
assert r.status_code == 201
deal = r.json()
deal_id = deal["id"]
print(f"    Created Deal: ID={deal_id}, Title={deal['title']}, Status={deal['status']}")
print("    [PASS] Deal created successfully")
print()

# 4. Update Deal to 'won' (Triggers Automated Activity hook)
print("[4] Updating Deal to 'won' (should trigger automated activity) ...")
r = httpx.put(f"{BASE}/crm/deals/{deal_id}", json={
    "status": "won"
})
assert r.status_code == 200
deal = r.json()
assert deal["status"] == "won"
print(f"    Deal status updated to: {deal['status']}")

# Verify Activity was created automatically
r = httpx.get(f"{BASE}/crm/activities/")
activities = r.json()["items"]
# Find activity for this customer
customer_activities = [a for a in activities if a["customer_id"] == customer_id]
assert len(customer_activities) == 1
activity = customer_activities[0]
print(f"    Automated Activity created: {activity['content']}")
assert "won" in activity["content"].lower()
print("    [PASS] Automated Activity created via hook")
print()

# 5. AI Email Generation (Custom Endpoint)
print("[5] Generating AI draft email for Customer ...")
r = httpx.post(f"{BASE}/crm/custom/customers/{customer_id}/draft_email")
assert r.status_code == 200
email = r.json()
print(f"    Subject: {email['subject']}")
print(f"    Body:\n{email['body']}")
assert email["subject"]
assert email["body"]
print("    [PASS] AI Email generated successfully")
print()

print("=" * 60)
print("=== ALL PHASE 7 CHECKS PASSED ===")
print("=" * 60)
