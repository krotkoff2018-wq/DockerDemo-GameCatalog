"""Streamlit frontend для лабораторной работы по Docker Compose."""

import html
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://backend:8000").rstrip("/")
STATUS_LABELS = {
    "planned": "🗓️ Планирую пройти",
    "playing": "🎮 Играю сейчас",
    "completed": "🏆 Пройдено",
}
STATUS_OPTIONS = list(STATUS_LABELS)

st.set_page_config(
    page_title="GameVault — Каталог видеоигр",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 1180px; padding-top: 1.7rem;}
      h1, h2, h3 {letter-spacing: -.02em;}
      [data-testid="stMetric"] {background: #17203910; padding: 15px; border-radius: 14px;}
      .hero {background: linear-gradient(115deg,#242b53,#503d81 58%,#7e4a93);
             border-radius: 22px; padding: 32px; margin-bottom: 16px; color: white;}
      .hero h1 {color: #ffffff !important; margin:0 0 9px 0; font-size: 2.75rem;}
      .hero p {color: #ebeafa; font-size: 1.08rem; margin:0;}
      .eyebrow {text-transform: uppercase; font-size: .73rem; font-weight: 700;
                letter-spacing: .16em; color: #d6c5fc; margin-bottom: 8px;}
      .game-meta {color: #7b7b93; font-size: .85rem;}
      .note {font-size: .86rem; color:#85859b;}
    </style>
    """,
    unsafe_allow_html=True,
)


def api(method: str, path: str, *, params=None, payload=None, show_errors=True):
    try:
        response = requests.request(
            method, f"{API_URL}{path}", params=params, json=payload, timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        detail = ""
        if exc.response is not None:
            try:
                detail = str(exc.response.json().get("detail", ""))
            except ValueError:
                detail = exc.response.text[:120]
        if show_errors:
            st.error(f"Ошибка обращения к API: {detail or str(exc)}")
        return None


def refresh_library():
    items = api("GET", "/library")
    if items is not None:
        st.session_state["library"] = items
    return items


def show_requirements(game: dict):
    st.caption(
        f"Минимальные требования (демо): RAM {game['min_ram_gb']} ГБ · "
        f"диск {game['min_storage_gb']} ГБ · VRAM {game['min_vram_gb']} ГБ"
    )


st.markdown(
    """<div class="hero"><div class="eyebrow">Docker Compose · Вариант №37</div>
    <h1>🎮 GameVault</h1>
    <p>Подберите видеоигры под возможности своего компьютера и соберите личную библиотеку.</p>
    </div>""",
    unsafe_allow_html=True,
)

search_tab, library_tab, about_tab = st.tabs(
    ["🔍 Подобрать игры", "📚 Моя библиотека", "ℹ️ Как устроено"]
)

with search_tab:
    st.subheader("Поиск по жанрам и требованиям ПК")
    st.write("Укажите доступные ресурсы компьютера: будут показаны игры с требованиями **не выше** заданных.")

    genres = api("GET", "/genres", show_errors=False) or []
    top_left, top_right = st.columns([2, 1])
    with top_left:
        search_query = st.text_input("Название игры", placeholder="Например, Hollow Knight")
    with top_right:
        genre = st.selectbox("Жанр", ["Все жанры", *genres])

    c1, c2, c3 = st.columns(3)
    with c1:
        ram = st.slider("Оперативная память (ГБ)", 0, 32, 8, step=1)
    with c2:
        storage = st.slider("Свободное место (ГБ)", 0, 200, 80, step=5)
    with c3:
        vram = st.slider("Видеопамять (ГБ)", 0, 16, 4, step=1)

    if st.button("🔍 Найти подходящие игры", type="primary", use_container_width=True):
        found = api(
            "GET", "/games",
            params={
                "genre": None if genre == "Все жанры" else genre,
                "query": search_query.strip() or None,
                "ram_gb": ram, "storage_gb": storage, "vram_gb": vram,
            },
        )
        if found is not None:
            st.session_state["search_result"] = found

    if "search_result" in st.session_state:
        result = st.session_state["search_result"]
        st.markdown(f"#### Найдено игр: {len(result)}")
        st.caption("CPU и GPU указаны справочно. В учебной фильтрации учитываются RAM, свободное место и VRAM.")
        if not result:
            st.info("Ничего не подошло. Попробуйте другой жанр или увеличьте доступные ресурсы.")
        else:
            saved_ids = {item["external_game_id"] for item in (st.session_state.get("library") or [])}
            for start in range(0, len(result), 2):
                columns = st.columns(2)
                for column, game in zip(columns, result[start:start + 2]):
                    with column:
                        with st.container(border=True):
                            safe_title = html.escape(game["title"])
                            st.markdown(f"### 🎯 {safe_title}")
                            st.caption(f"{game['genre']} · {game['release_year']}")
                            show_requirements(game)
                            st.write(f"**CPU:** {game['min_cpu']}  |  **GPU:** {game['min_gpu']}")
                            already_saved = game["id"] in saved_ids
                            if st.button(
                                "✓ Уже в библиотеке" if already_saved else "＋ В мою библиотеку",
                                key=f"add_game_{game['id']}",
                                disabled=already_saved,
                                use_container_width=True,
                            ):
                                added = api("POST", "/library", payload={"game_id": game["id"]})
                                if added is not None:
                                    saved_ids.add(game["id"])
                                    refresh_library()
                                    st.success("Игра добавлена! Откройте вкладку «Моя библиотека».")

with library_tab:
    st.subheader("Личная игровая библиотека")
    st.write("Записи хранятся в PostgreSQL и не исчезают при обычной остановке Docker Compose.")
    if st.button("📚 Показать / обновить библиотеку", type="primary", use_container_width=True):
        refresh_library()

    if "library" not in st.session_state:
        refresh_library()

    library = st.session_state.get("library", [])
    m1, m2, m3 = st.columns(3)
    m1.metric("Всего игр", len(library))
    m2.metric("Играю сейчас", sum(g["status"] == "playing" for g in library))
    m3.metric("Пройдено", sum(g["status"] == "completed" for g in library))

    if not library:
        st.info("В библиотеке пока нет игр. Перейдите на вкладку поиска и добавьте первую.")
    for game in library:
        with st.container(border=True):
            left, right = st.columns([3, 2])
            with left:
                st.markdown(f"#### {html.escape(game['title'])}")
                st.caption(f"{game['genre']} · {game['release_year']} · {STATUS_LABELS.get(game['status'], game['status'])}")
                show_requirements(game)
                if game["rating"] is not None:
                    st.write(f"⭐ Моя оценка: **{game['rating']}/10**")
            with right:
                with st.expander("Изменить запись"):
                    status = st.selectbox(
                        "Статус", STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(game["status"]),
                        format_func=lambda value: STATUS_LABELS[value],
                        key=f"status_{game['id']}",
                    )
                    rating = st.selectbox(
                        "Моя оценка", [None, *range(1, 11)],
                        index=0 if game["rating"] is None else game["rating"],
                        format_func=lambda value: "Без оценки" if value is None else f"{value}/10",
                        key=f"rating_{game['id']}",
                    )
                    if st.button("💾 Сохранить", key=f"update_{game['id']}"):
                        updated = api("PATCH", f"/library/{game['id']}", payload={"status": status, "rating": rating})
                        if updated is not None:
                            refresh_library()
                            st.success("Изменения сохранены. Данные обновятся при следующем отображении.")
                    if st.button("🗑️ Удалить из библиотеки", key=f"delete_{game['id']}"):
                        deleted = api("DELETE", f"/library/{game['id']}")
                        if deleted is not None:
                            refresh_library()
                            st.success("Игра удалена. Данные обновятся при следующем отображении.")

with about_tab:
    st.subheader("Архитектура из четырёх контейнеров")
    st.code(
        "Браузер → frontend (Streamlit :8501)\n"
        "                     ↓ HTTP\n"
        "             backend (FastAPI :8000)\n"
        "                ↙           ↘\n"
        "    db (PostgreSQL :5432)    web-service (FastAPI :8001)",
        language="text",
    )
    st.write("**Действия:** поиск через отдельный веб-сервис; добавление, чтение, редактирование и удаление записей через PostgreSQL.")
    st.info("Минимальные характеристики игр в демонстрационном наборе приблизительные, не являются официальными системными требованиями.")
    st.link_button("Открыть документацию Backend API", "http://localhost:8000/docs")
