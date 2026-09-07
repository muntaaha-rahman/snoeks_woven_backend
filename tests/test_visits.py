SAMPLE_VISIT = {
    "customer_name": "Jan Jansen",
    "address": "Kerkstraat 1",
    "postal_code": "1234 AB",
    "city": "Utrecht",
    "phone": "0612345678",
    "email": "jan@example.com",
    "visit_date": "2026-09-07",
    "surveyor_name": "Piet",
    "property_notes": "Parking in the back",
    "rooms": [
        {
            "name": "Living room",
            "window_treatments": [
                {
                    "width_mm": 1200,
                    "height_mm": 1500,
                    "product": "roller_blind",
                    "fabric_colour_sample": "RAL 9010",
                    "operating_side": "left",
                    "operating_type": "chain",
                    "mounting": "wall",
                }
            ],
            "flooring_sections": [
                {"length_m": 4.2, "width_m": 3.5, "subfloor_type": "concrete"},
                {"length_m": 1.1, "width_m": 0.8, "subfloor_type": "concrete"},
            ],
            "insect_screens": [],
            "sun_shadings": [
                {"width_mm": 2000, "height_projection_mm": 2500, "mounting_surface": "frame"}
            ],
        }
    ],
}


def test_create_visit_computes_area_and_attempts_email(client):
    r = client.post("/visits", json=SAMPLE_VISIT)
    assert r.status_code == 200
    data = r.json()
    assert data["rooms"][0]["flooring_sections"][0]["area_m2"] == 14.7
    # No SMTP server in test env, so the send should fail gracefully and record the error.
    assert data["email_sent"] is False
    assert data["email_error"]


def test_list_search_and_filter(client):
    client.post("/visits", json=SAMPLE_VISIT)
    other = {**SAMPLE_VISIT, "customer_name": "Marie de Vries", "city": "Amsterdam"}
    client.post("/visits", json=other)

    assert len(client.get("/visits").json()) == 2
    assert len(client.get("/visits", params={"search": "Jansen"}).json()) == 1
    assert len(client.get("/visits", params={"city": "Amsterdam"}).json()) == 1
    assert len(client.get("/visits", params={"search": "Nobody"}).json()) == 0


def test_get_update_delete_visit(client):
    created = client.post("/visits", json=SAMPLE_VISIT).json()
    visit_id = created["id"]

    fetched = client.get(f"/visits/{visit_id}")
    assert fetched.status_code == 200

    updated_payload = {**SAMPLE_VISIT, "customer_name": "Renamed Customer"}
    updated = client.put(f"/visits/{visit_id}", json=updated_payload)
    assert updated.status_code == 200
    assert updated.json()["customer_name"] == "Renamed Customer"

    deleted = client.delete(f"/visits/{visit_id}")
    assert deleted.status_code == 204
    assert client.get(f"/visits/{visit_id}").status_code == 404


def test_pdf_download(client):
    visit_id = client.post("/visits", json=SAMPLE_VISIT).json()["id"]
    pdf = client.get(f"/visits/{visit_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"


def test_resend_email(client):
    visit_id = client.post("/visits", json=SAMPLE_VISIT).json()["id"]
    resent = client.post(f"/visits/{visit_id}/resend-email")
    assert resent.status_code == 200
    assert resent.json()["email_sent"] is False


def test_photo_upload_requires_valid_owner(client):
    r = client.post(
        "/photos",
        params={"owner_type": "window_treatment", "owner_id": "does-not-exist"},
        files={"file": ("test.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert r.status_code == 404


def test_inline_photo_on_create(client):
    # 1x1 transparent PNG, base64-encoded, as the browser's FileReader would produce.
    tiny_png = (
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4"
        "nGNgAAIAAAUAAen63NgAAAAASUVORK5CYII="
    )
    payload = {**SAMPLE_VISIT, "rooms": [{**SAMPLE_VISIT["rooms"][0]}]}
    payload["rooms"][0] = {
        **SAMPLE_VISIT["rooms"][0],
        "window_treatments": [
            {**SAMPLE_VISIT["rooms"][0]["window_treatments"][0], "new_photos": [tiny_png]}
        ],
    }

    created = client.post("/visits", json=payload).json()
    item = created["rooms"][0]["window_treatments"][0]
    assert len(item["photos"]) == 1
    assert item["photos"][0]["file_path"].startswith("/uploads/")
    assert "new_photos" not in item


def test_photo_upload_success(client):
    created = client.post("/visits", json=SAMPLE_VISIT).json()
    item_id = created["rooms"][0]["window_treatments"][0]["id"]

    r = client.post(
        "/photos",
        params={"owner_type": "window_treatment", "owner_id": item_id},
        files={"file": ("test.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert r.status_code == 200
    assert r.json()["file_path"].startswith("/uploads/")

    fetched = client.get(f"/visits/{created['id']}").json()
    assert len(fetched["rooms"][0]["window_treatments"][0]["photos"]) == 1
