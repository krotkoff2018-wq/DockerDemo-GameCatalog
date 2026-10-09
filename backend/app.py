"""REST API: оркестрация каталога игр и личной PostgreSQL-библиотеки."""

import os
from typing import Literal

import httpx
import psycopg
from fastapi import FastAPI, HTTPException, Query
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

app = FastAPI(
    title="Каталог видеоигр — Backend API",
    version="1.0.0",
    description="Вариант №37: отдельный каталог игр + личная библиотека PostgreSQL",
)

WEB_SERVICE_URL = os.getenv("WEB_SERVICE_URL", "http://web-service:8001").rstrip("/")
GameStatus = Literal["planned", "playing", "completed"]


class LibraryCreate(BaseModel):
    game_id: int = Field(ge=1)
    status: GameStatus = "planned"


class LibraryUpdate(BaseModel):
    status: GameStatus | None = None
    rating: int | None = Field(default=None, ge=1, le=10)


def connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "games_db"),
        user=os.getenv("DB_USER", "games_user"),
        password=os.getenv("DB_PASSWORD", ""),
        row_factory=dict_row,
    )


def request_catalog(path: str, params: dict | None = None):
    """Frontend никогда не обращается к web-service напрямую."""
    try:
        response = httpx.get(f"{WEB_SERVICE_URL}{path}", params=params, timeout=8)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Игра не найдена в каталоге")
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Сервис каталога игр недоступен") from exc


@app.get("/health")
def health():
    return {"status": "ok", "service": "backend"}


@app.get("/genres")
def list_genres():
    return request_catalog("/genres")


@app.get("/games")
def search_games(
    genre: str | None = None,
    query: str | None = None,
    ram_gb: int | None = Query(default=None, ge=0),
    storage_gb: int | None = Query(default=None, ge=0),
    vram_gb: int | None = Query(default=None, ge=0),
):
    """Поиск игр, подходящих по заданным ресурсам компьютера."""
    params = {
        "genre": genre, "query": query, "max_ram_gb": ram_gb,
        "max_storage_gb": storage_gb, "max_vram_gb": vram_gb,
    }
    return request_catalog("/games", {k: v for k, v in params.items() if v is not None})


@app.get("/library")
def list_library():
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, external_game_id, title, genre, release_year,
                          min_ram_gb, min_storage_gb, min_vram_gb,
                          status, rating, added_at
                   FROM library_games ORDER BY added_at DESC, id DESC"""
            )
            return cur.fetchall()


@app.post("/library", status_code=201)
def add_to_library(item: LibraryCreate):
    game = request_catalog(f"/games/{item.game_id}")
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO library_games
                       (external_game_id, title, genre, release_year,
                        min_ram_gb, min_storage_gb, min_vram_gb, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (external_game_id) DO NOTHING
                   RETURNING id, title, genre, status, rating""",
                (
                    game["id"], game["title"], game["genre"],
                    game["release_year"], game["min_ram_gb"],
                    game["min_storage_gb"], game["min_vram_gb"], item.status,
                ),
            )
            record = cur.fetchone()
            if record is None:
                raise HTTPException(status_code=409, detail="Игра уже находится в библиотеке")
            return record


@app.patch("/library/{record_id}")
def update_library(record_id: int, item: LibraryUpdate):
    updates = item.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="Укажите поля для изменения")
    if "status" in updates and updates["status"] is None:
        raise HTTPException(status_code=422, detail="Статус не может быть пустым")

    # Имена колонок приходят только из валидированной модели, не из SQL-строки клиента.
    assignments = ", ".join(f"{column} = %s" for column in updates)
    values = [*updates.values(), record_id]
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE library_games SET {assignments} WHERE id = %s "
                "RETURNING id, title, genre, status, rating",
                values,
            )
            record = cur.fetchone()
            if record is None:
                raise HTTPException(status_code=404, detail="Запись не найдена")
            return record


@app.delete("/library/{record_id}")
def delete_from_library(record_id: int):
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM library_games WHERE id = %s RETURNING id", (record_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Запись не найдена")
            return {"message": "Игра удалена из библиотеки", "id": record_id}
