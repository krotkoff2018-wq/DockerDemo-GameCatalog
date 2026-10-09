"""Локальные тесты сервиса каталога без Docker и PostgreSQL."""

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

module_path = Path(__file__).resolve().parents[1] / "web-service" / "app.py"
spec = importlib.util.spec_from_file_location("game_service", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
client = TestClient(module.app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_catalog_contains_games():
    result = client.get("/games")
    assert result.status_code == 200
    assert len(result.json()) >= 20


def test_genre_filter():
    result = client.get("/games", params={"genre": "RPG"}).json()
    assert len(result) >= 2
    assert all(game["genre"] == "RPG" for game in result)


def test_min_requirements_fit_available_resources():
    result = client.get(
        "/games", params={"max_ram_gb": 4, "max_storage_gb": 10, "max_vram_gb": 1}
    ).json()
    assert result
    assert all(game["min_ram_gb"] <= 4 for game in result)
    assert all(game["min_storage_gb"] <= 10 for game in result)
    assert all(game["min_vram_gb"] <= 1 for game in result)


def test_search_by_title_case_insensitive():
    result = client.get("/games", params={"query": "STARDEW"}).json()
    assert len(result) == 1
    assert result[0]["title"] == "Stardew Valley"


def test_game_details_and_not_found():
    assert client.get("/games/1").json()["title"] == "Stardew Valley"
    assert client.get("/games/9999").status_code == 404


def test_invalid_requirements_rejected():
    assert client.get("/games", params={"max_ram_gb": -1}).status_code == 422
