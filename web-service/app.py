"""Локальный справочный web-сервис для варианта №37.

Значения требований приближённые и приведены только для учебного примера.
Для настоящих рекомендаций нужно брать официальные требования игр.
"""

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Game catalog web service", version="1.0.0")

# id, название, жанр, год, RAM, диск, VRAM, CPU, GPU.
_RECORDS = [
    (1, "Stardew Valley", "Симулятор", 2016, 2, 1, 0, "2 ГГц", "Встроенная графика"),
    (2, "Terraria", "Приключения", 2011, 2, 1, 0, "2 ГГц", "Встроенная графика"),
    (3, "Portal 2", "Головоломка", 2011, 2, 8, 0, "2 ГГц", "Встроенная графика"),
    (4, "Hollow Knight", "Платформер", 2017, 4, 9, 1, "2 ГГц", "GeForce 9800 GTX"),
    (5, "Hades", "Рогалик", 2020, 4, 15, 1, "Dual Core 2.4 ГГц", "Видеокарта 1 ГБ"),
    (6, "Celeste", "Платформер", 2018, 2, 2, 0, "2 ГГц", "Встроенная графика"),
    (7, "Dead Cells", "Рогалик", 2018, 2, 2, 1, "Intel i5", "Видеокарта 1 ГБ"),
    (8, "Dota 2", "Стратегия", 2013, 4, 60, 1, "Dual Core 2.8 ГГц", "Видеокарта 1 ГБ"),
    (9, "Cuphead", "Платформер", 2017, 3, 4, 1, "Intel Core2 Duo", "Видеокарта 1 ГБ"),
    (10, "Undertale", "RPG", 2015, 2, 1, 0, "2 ГГц", "Встроенная графика"),
    (11, "Subnautica", "Приключения", 2018, 8, 20, 2, "Intel i5", "GeForce GTX 550 Ti"),
    (12, "Minecraft: Java Edition", "Симулятор", 2011, 4, 4, 1, "Intel Core i3", "Видеокарта 1 ГБ"),
    (13, "Factorio", "Стратегия", 2020, 8, 3, 1, "Quad Core 3 ГГц", "Видеокарта 1 ГБ"),
    (14, "Euro Truck Simulator 2", "Симулятор", 2012, 8, 25, 2, "Quad Core 3 ГГц", "Видеокарта 2 ГБ"),
    (15, "Slay the Spire", "Рогалик", 2019, 2, 1, 0, "2 ГГц", "Встроенная графика"),
    (16, "Oxygen Not Included", "Симулятор", 2019, 4, 2, 1, "Dual Core 2 ГГц", "Видеокарта 1 ГБ"),
    (17, "Ori and the Blind Forest", "Платформер", 2015, 4, 8, 1, "Intel Core2 Duo", "Видеокарта 1 ГБ"),
    (18, "Disco Elysium", "RPG", 2019, 4, 20, 1, "Intel Core2 Duo", "Видеокарта 1 ГБ"),
    (19, "Outer Wilds", "Приключения", 2019, 6, 8, 2, "Intel Core i5", "Видеокарта 2 ГБ"),
    (20, "The Witcher 3: Wild Hunt", "RPG", 2015, 8, 50, 2, "Intel Core i5", "GeForce GTX 660"),
    (21, "Cyberpunk 2077", "RPG", 2020, 12, 70, 6, "Intel Core i7", "GeForce GTX 1060"),
    (22, "Cities: Skylines", "Симулятор", 2015, 8, 4, 2, "Intel Core i7", "Видеокарта 2 ГБ"),
    (23, "Baldur's Gate 3", "RPG", 2023, 8, 150, 4, "Intel Core i5", "GeForce GTX 970"),
    (24, "Elden Ring", "Экшен", 2022, 12, 60, 3, "Intel Core i5", "GeForce GTX 1060"),
]

GAMES = [
    {
        "id": row[0], "title": row[1], "genre": row[2],
        "release_year": row[3], "min_ram_gb": row[4],
        "min_storage_gb": row[5], "min_vram_gb": row[6],
        "min_cpu": row[7], "min_gpu": row[8],
    }
    for row in _RECORDS
]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/genres")
def genres():
    return sorted({game["genre"] for game in GAMES})


@app.get("/games")
def find_games(
    genre: str | None = None,
    query: str | None = None,
    max_ram_gb: int | None = Query(default=None, ge=0),
    max_storage_gb: int | None = Query(default=None, ge=0),
    max_vram_gb: int | None = Query(default=None, ge=0),
):
    """Отбор игр, которые помещаются в доступные ресурсы ПК.

    Используются упрощенные демо-характеристики; CPU/GPU выводятся справочно.
    """
    result = GAMES
    if genre and genre != "Все жанры":
        result = [g for g in result if g["genre"].casefold() == genre.casefold()]
    if query:
        result = [g for g in result if query.casefold() in g["title"].casefold()]
    if max_ram_gb is not None:
        result = [g for g in result if g["min_ram_gb"] <= max_ram_gb]
    if max_storage_gb is not None:
        result = [g for g in result if g["min_storage_gb"] <= max_storage_gb]
    if max_vram_gb is not None:
        result = [g for g in result if g["min_vram_gb"] <= max_vram_gb]
    return result


@app.get("/games/{game_id}")
def game_details(game_id: int):
    game = next((g for g in GAMES if g["id"] == game_id), None)
    if game is None:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    return game
