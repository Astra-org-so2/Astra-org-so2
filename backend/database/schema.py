"""
Схема базы данных SQLite
"""

SCHEMA = """
-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    language_code TEXT DEFAULT 'ru',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Игровой прогресс пользователя
CREATE TABLE IF NOT EXISTS user_progress (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    income_per_hour REAL DEFAULT 10,
    guests_per_hour INTEGER DEFAULT 2,
    total_earned REAL DEFAULT 0,
    last_income_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Улучшения
CREATE TABLE IF NOT EXISTS upgrades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL, -- 'equipment', 'staff', 'interior'
    base_cost REAL NOT NULL,
    cost_multiplier REAL DEFAULT 1.15,
    income_bonus REAL DEFAULT 0,
    guests_bonus INTEGER DEFAULT 0,
    description TEXT,
    icon TEXT
);

-- Улучшения пользователя
CREATE TABLE IF NOT EXISTS user_upgrades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    upgrade_id INTEGER NOT NULL,
    level INTEGER DEFAULT 0,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (upgrade_id) REFERENCES upgrades(id) ON DELETE CASCADE,
    UNIQUE(user_id, upgrade_id)
);

-- Достижения
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    icon TEXT,
    condition_type TEXT NOT NULL, -- 'total_earned', 'upgrades_count', 'guests_served'
    condition_value REAL NOT NULL,
    reward_amount REAL DEFAULT 0
);

-- Достижения пользователя
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id INTEGER NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE,
    UNIQUE(user_id, achievement_id)
);

-- Мини-игры
CREATE TABLE IF NOT EXISTS minigame_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    game_type TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    reward REAL DEFAULT 0,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Статистика групп (для лидерборда)
CREATE TABLE IF NOT EXISTS group_stats (
    group_id INTEGER PRIMARY KEY,
    group_name TEXT,
    member_count INTEGER DEFAULT 0,
    total_earnings REAL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_upgrades_user_id ON user_upgrades(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_minigame_attempts_user_id ON minigame_attempts(user_id);
"""

# Начальные данные для улучшений
INITIAL_UPGRADES = """
INSERT OR IGNORE INTO upgrades (name, category, base_cost, income_bonus, guests_bonus, description, icon) VALUES
-- Оборудование
('Улучшенный гриль', 'equipment', 50, 1.0, 0, 'Готовит бургеры на 10% быстрее', '🍔'),
('Профессиональный фритюр', 'equipment', 100, 2.0, 0, 'Картофель фри премиум качества', '🍟'),
('Автоматическая кофемашина', 'equipment', 150, 1.5, 1, 'Готовит кофе без участия бариста', '☕'),
('Холодильная камера', 'equipment', 200, 0.5, 0, 'Продукты дольше остаются свежими', '❄️'),
('Конвейерная печь', 'equipment', 500, 5.0, 0, 'Выпекает булочки непрерывно', '🔥'),

-- Персонал
('Кассир', 'staff', 75, 0.5, 2, 'Обслуживает клиентов быстрее', '👨‍💼'),
('Повар', 'staff', 120, 3.0, 0, 'Готовит качественнее и быстрее', '👨‍🍳'),
('Уборщик', 'staff', 60, 0, 1, 'Поддерживает чистоту', '🧹'),
('Менеджер', 'staff', 300, 2.0, 3, 'Оптимизирует рабочие процессы', '👔'),
('Маркетолог', 'staff', 250, 1.0, 5, 'Привлекает больше клиентов', '📢'),

-- Интерьер
('Удобные кресла', 'interior', 80, 0, 2, 'Клиенты задерживаются дольше', '🪑'),
('Современный дизайн', 'interior', 200, 1.0, 3, 'Привлекает молодежь', '🎨'),
('Детская зона', 'interior', 150, 0.5, 4, 'Семьи с детьми', '🎪'),
('Wi-Fi зона', 'interior', 100, 0, 2, 'Для фрилансеров', '📶'),
('Летняя терраса', 'interior', 400, 2.0, 5, 'Дополнительные места', '🌳');
"""

# Начальные достижения
INITIAL_ACHIEVEMENTS = """
INSERT OR IGNORE INTO achievements (name, description, condition_type, condition_value, reward_amount, icon) VALUES
('Первые деньги', 'Заработать 100$', 'total_earned', 100, 10, '💵'),
('Малый бизнес', 'Заработать 1000$', 'total_earned', 1000, 50, '💰'),
('Средний бизнес', 'Заработать 10000$', 'total_earned', 10000, 200, '💎'),
('Корпорация', 'Заработать 100000$', 'total_earned', 100000, 1000, '🏢'),
('Магнат', 'Заработать 1000000$', 'total_earned', 1000000, 5000, '👑'),

('Первое улучшение', 'Купить любое улучшение', 'upgrades_count', 1, 5, '⭐'),
('Энтузиаст', 'Купить 5 улучшений', 'upgrades_count', 5, 25, '🌟'),
('Модернизатор', 'Купить 15 улучшений', 'upgrades_count', 15, 100, '✨'),
('Перфекционист', 'Купить все улучшения', 'upgrades_count', 15, 500, '🏆'),

('Первый клиент', 'Обслужить 10 гостей', 'guests_served', 10, 5, '👥'),
('Популярное место', 'Обслужить 100 гостей', 'guests_served', 100, 20, '👫'),
('Городская легенда', 'Обслужить 1000 гостей', 'guests_served', 1000, 100, '👨‍👩‍👧‍👦');
"""
