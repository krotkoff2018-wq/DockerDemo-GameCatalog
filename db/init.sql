-- Таблица личной библиотеки; доступ осуществляется через backend.
CREATE TABLE IF NOT EXISTS library_games (
    id SERIAL PRIMARY KEY,
    external_game_id INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL,
    genre TEXT NOT NULL,
    release_year INTEGER NOT NULL,
    min_ram_gb INTEGER NOT NULL CHECK (min_ram_gb >= 0),
    min_storage_gb INTEGER NOT NULL CHECK (min_storage_gb >= 0),
    min_vram_gb INTEGER NOT NULL CHECK (min_vram_gb >= 0),
    status TEXT NOT NULL DEFAULT 'planned'
        CHECK (status IN ('planned', 'playing', 'completed')),
    rating INTEGER CHECK (rating BETWEEN 1 AND 10),
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Учебные примеры при ПЕРВОЙ инициализации пустого volume.
INSERT INTO library_games
    (external_game_id, title, genre, release_year, min_ram_gb,
     min_storage_gb, min_vram_gb, status, rating)
VALUES
    (1, 'Stardew Valley', 'Симулятор', 2016, 2, 1, 0, 'playing', 9),
    (4, 'Hollow Knight', 'Платформер', 2017, 4, 9, 1, 'completed', 10),
    (11, 'Subnautica', 'Приключения', 2018, 8, 20, 2, 'planned', NULL)
ON CONFLICT (external_game_id) DO NOTHING;
