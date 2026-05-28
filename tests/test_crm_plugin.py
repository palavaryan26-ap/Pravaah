"""Integration tests for the CRM plugin."""

def test_create_customer(client):
    """Test creating a customer triggers the AI lead scoring hook."""
    response = client.post("/crm/customers/", json={
        "name": "Pytest Corp",
        "email": "test@pytest.org",
        "company": "Pytest Inc"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Pytest Corp"
    assert "ai_lead_score" in data


def test_create_and_win_deal(client):
    """Test that winning a deal automatically creates an Activity."""
    # 1. Create customer
    response = client.post("/crm/customers/", json={
        "name": "Deal Corp",
        "email": "deal@pytest.org",
        "company": "Deal Inc"
    })
    customer_id = response.json()["id"]

    # 2. Create deal
    response = client.post("/crm/deals/", json={
        "title": "Big Deal",
        "amount": 10000.0,
        "customer_id": customer_id
    })
    assert response.status_code == 201
    deal_id = response.json()["id"]

    # 3. Update to won
    response = client.put(f"/crm/deals/{deal_id}", json={
        "status": "won"
    })
    assert response.status_code == 200

    # 4. Verify Activity was automatically created
    response = client.get("/crm/activities/")
    assert response.status_code == 200
    activities = [a for a in response.json()["items"] if a["customer_id"] == customer_id]
    assert len(activities) == 1
    assert "won" in activities[0]["content"].lower()


def test_draft_email(client):
    """Test the custom AI endpoint for drafting emails."""
    # 1. Create customer
    response = client.post("/crm/customers/", json={
        "name": "Email Corp",
        "email": "email@pytest.org",
        "company": "Email Inc"
    })
    customer_id = response.json()["id"]

    # 2. Call custom AI route
    response = client.post(f"/crm/custom/customers/{customer_id}/draft_email")
    assert response.status_code == 200
    data = response.json()
    assert "subject" in data
    assert "body" in data
