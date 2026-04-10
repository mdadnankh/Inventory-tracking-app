def test_create_product_and_list_products(client):
    r = client.post(
        "/api/products",
        json={"sku": "SKU-1", "name": "Widget", "low_stock_threshold": 2},
    )
    assert r.status_code == 201
    created = r.get_json()
    assert created["sku"] == "SKU-1"
    assert created["current_stock"] == 0

    r = client.get("/api/products")
    assert r.status_code == 200
    products = r.get_json()
    assert len(products) == 1
    assert products[0]["sku"] == "SKU-1"
    assert products[0]["current_stock"] == 0


def test_unique_sku_conflict(client):
    r1 = client.post("/api/products", json={"sku": "DUP", "name": "A"})
    assert r1.status_code == 201

    r2 = client.post("/api/products", json={"sku": "DUP", "name": "B"})
    assert r2.status_code == 409
    body = r2.get_json()
    assert body["error"]["code"] == "conflict"


def test_receive_increases_stock_and_movements_list(client):
    r = client.post("/api/products", json={"sku": "SKU-1", "name": "Widget"})
    pid = r.get_json()["id"]

    r = client.post(f"/api/products/{pid}/movements", json={"type": "receive", "quantity": 5})
    assert r.status_code == 201
    body = r.get_json()
    assert body["current_stock"] == 5

    r = client.get("/api/products")
    assert r.get_json()[0]["current_stock"] == 5

    r = client.get(f"/api/products/{pid}/movements")
    assert r.status_code == 200
    res = r.get_json()
    assert "items" in res
    moves = res["items"]
    assert len(moves) == 1
    assert moves[0]["type"] == "receive"
    assert moves[0]["quantity"] == 5


def test_ship_cannot_make_stock_negative(client):
    r = client.post("/api/products", json={"sku": "SKU-1", "name": "Widget"})
    pid = r.get_json()["id"]

    r = client.post(f"/api/products/{pid}/movements", json={"type": "receive", "quantity": 3})
    assert r.status_code == 201

    r = client.post(f"/api/products/{pid}/movements", json={"type": "ship", "quantity": 10})
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"]["code"] == "invariant_violation"


def test_low_stock_alerts(client):
    r = client.post("/api/products", json={"sku": "SKU-LOW", "name": "Low", "low_stock_threshold": 10})
    pid = r.get_json()["id"]

    # Current stock becomes 5, threshold is 10 => should be in low-stock list.
    r = client.post(f"/api/products/{pid}/movements", json={"type": "receive", "quantity": 5})
    assert r.status_code == 201

    r = client.get("/api/alerts/low-stock")
    assert r.status_code == 200
    items = r.get_json()
    assert len(items) == 1
    assert items[0]["sku"] == "SKU-LOW"
    assert items[0]["current_stock"] == 5

