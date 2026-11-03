"""
Tests for restocking order endpoints.
"""
from datetime import datetime, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def reset_restock_orders():
    """Restock orders are module-level state; isolate each test."""
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


class TestRestockOrders:
    def test_demand_includes_cost_and_lead_time(self, client):
        data = client.get("/api/demand").json()
        for item in data:
            assert item["unit_cost"] > 0
            assert item["lead_time_days"] > 0

    def test_list_empty_initially(self, client):
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order_computes_totals_and_lead_time(self, client):
        payload = {"items": [
            {"item_sku": "WDG-001", "quantity": 10},  # 12.50, 10 days
            {"item_sku": "GSK-203", "quantity": 100},  # 2.40, 5 days
        ]}
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201
        order = response.json()

        assert order["order_number"] == f"RST-{datetime.now().year}-0001"
        assert order["status"] == "Submitted"
        assert order["total_cost"] == pytest.approx(125.0 + 240.0)
        assert order["lead_time_days"] == 10
        submitted = datetime.fromisoformat(order["submitted_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert expected - submitted == timedelta(days=10)
        assert order["items"][0]["item_name"] == "Industrial Widget Type A"
        assert order["items"][0]["line_total"] == pytest.approx(125.0)

    def test_created_order_is_listed_newest_first(self, client):
        client.post("/api/restock-orders", json={"items": [{"item_sku": "WDG-001", "quantity": 1}]})
        client.post("/api/restock-orders", json={"items": [{"item_sku": "FLT-405", "quantity": 1}]})
        orders = client.get("/api/restock-orders").json()
        assert [o["order_number"][-4:] for o in orders] == ["0002", "0001"]

    def test_unknown_sku_rejected(self, client):
        response = client.post("/api/restock-orders", json={"items": [{"item_sku": "NOPE-999", "quantity": 5}]})
        assert response.status_code == 400
        assert main.restock_orders == []

    @pytest.mark.parametrize("payload", [
        {"items": []},
        {"items": [{"item_sku": "WDG-001", "quantity": 0}]},
        {"items": [{"item_sku": "WDG-001", "quantity": -3}]},
        {},
    ])
    def test_invalid_payload_rejected(self, client, payload):
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 422
