import json
import pytest
from app.models.user import User
from app.models.gamification import UserGamification
from app.extensions import db

def test_senafonica_requires_login(client):
    res = client.get("/senafonica")
    assert res.status_code in (302, 401)

def test_senafonica_page_authenticated(login_client):
    auth_client, user_id = login_client()
    res = auth_client.get("/senafonica")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "SENAFÓNICA" in html
    assert "senafonica_audio.js" in html
    assert "senafonica_game.js" in html
    assert "senafonica.css" in html

def test_senafonica_api_data(login_client):
    auth_client, user_id = login_client()
    res = auth_client.get("/api/senafonica/data")
    assert res.status_code == 200
    data = res.get_json()
    assert "levels" in data
    assert "intervals" in data
    assert "scales" in data
    assert "theory_questions" in data
    assert "shop_items" in data
    assert len(data["levels"]) >= 10
    assert len(data["theory_questions"]) >= 10

def test_senafonica_api_sync(app, login_client):
    auth_client, user_id = login_client()
    payload = {
        "xp_earned": 50,
        "coins_earned": 10,
        "correct_count": 5,
        "total_count": 5
    }
    res = auth_client.post(
        "/api/senafonica/sync",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["total_xp"] == 50
    assert data["coins"] == 10
