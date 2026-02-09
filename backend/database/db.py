"""
Менеджер базы данных
"""
import aiosqlite
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from .schema import SCHEMA, INITIAL_UPGRADES, INITIAL_ACHIEVEMENTS


logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Подключение к базе данных"""
        # Создаем директорию если её нет
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA foreign_keys = ON")
        logger.info(f"Connected to database: {self.db_path}")
    
    async def disconnect(self):
        """Закрытие подключения"""
        if self._connection:
            await self._connection.close()
            logger.info("Database connection closed")
    
    async def init_db(self):
        """Инициализация структуры базы данных"""
        async with self._connection.executescript(SCHEMA) as cursor:
            await self._connection.commit()
        
        # Добавляем начальные данные
        await self._connection.executescript(INITIAL_UPGRADES)
        await self._connection.executescript(INITIAL_ACHIEVEMENTS)
        await self._connection.commit()
        
        logger.info("Database schema initialized")
    
    async def execute(self, query: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """Выполнение SQL запроса"""
        cursor = await self._connection.execute(query, parameters)
        await self._connection.commit()
        return cursor
    
    async def fetchone(self, query: str, parameters: tuple = ()) -> Optional[Dict]:
        """Получить одну запись"""
        async with self._connection.execute(query, parameters) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def fetchall(self, query: str, parameters: tuple = ()) -> List[Dict]:
        """Получить все записи"""
        async with self._connection.execute(query, parameters) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # === USER METHODS ===
    
    async def create_user(self, user_id: int, username: str = None, 
                         first_name: str = None, language_code: str = 'ru') -> bool:
        """Создание нового пользователя"""
        try:
            await self.execute(
                """INSERT INTO users (user_id, username, first_name, language_code)
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, first_name, language_code)
            )
            
            # Создаем начальный прогресс
            await self.execute(
                """INSERT INTO user_progress (user_id, balance, income_per_hour, guests_per_hour)
                   VALUES (?, 0, 10, 2)""",
                (user_id,)
            )
            
            logger.info(f"Created new user: {user_id}")
            return True
        except aiosqlite.IntegrityError:
            logger.warning(f"User {user_id} already exists")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить данные пользователя"""
        return await self.fetchone(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
    
    async def update_last_active(self, user_id: int):
        """Обновить время последней активности"""
        await self.execute(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
    
    # === PROGRESS METHODS ===
    
    async def get_user_progress(self, user_id: int) -> Optional[Dict]:
        """Получить игровой прогресс пользователя"""
        return await self.fetchone(
            "SELECT * FROM user_progress WHERE user_id = ?",
            (user_id,)
        )
    
    async def update_balance(self, user_id: int, amount: float, 
                            update_total: bool = True) -> bool:
        """Обновить баланс пользователя"""
        if update_total:
            await self.execute(
                """UPDATE user_progress 
                   SET balance = balance + ?, total_earned = total_earned + ?
                   WHERE user_id = ?""",
                (amount, amount, user_id)
            )
        else:
            await self.execute(
                "UPDATE user_progress SET balance = balance + ? WHERE user_id = ?",
                (amount, user_id)
            )
        return True
    
    async def update_income_stats(self, user_id: int, income_per_hour: float, 
                                  guests_per_hour: int):
        """Обновить статистику дохода"""
        await self.execute(
            """UPDATE user_progress 
               SET income_per_hour = ?, guests_per_hour = ?
               WHERE user_id = ?""",
            (income_per_hour, guests_per_hour, user_id)
        )
    
    async def update_last_income_collected(self, user_id: int):
        """Обновить время последнего сбора дохода"""
        await self.execute(
            """UPDATE user_progress 
               SET last_income_collected = CURRENT_TIMESTAMP
               WHERE user_id = ?""",
            (user_id,)
        )
    
    # === UPGRADES METHODS ===
    
    async def get_all_upgrades(self) -> List[Dict]:
        """Получить все доступные улучшения"""
        return await self.fetchall("SELECT * FROM upgrades ORDER BY category, base_cost")
    
    async def get_user_upgrades(self, user_id: int) -> List[Dict]:
        """Получить улучшения пользователя"""
        return await self.fetchall(
            """SELECT uu.*, u.name, u.category, u.base_cost, u.cost_multiplier,
                      u.income_bonus, u.guests_bonus, u.description, u.icon
               FROM user_upgrades uu
               JOIN upgrades u ON uu.upgrade_id = u.id
               WHERE uu.user_id = ?""",
            (user_id,)
        )
    
    async def get_user_upgrade_level(self, user_id: int, upgrade_id: int) -> int:
        """Получить уровень улучшения пользователя"""
        result = await self.fetchone(
            "SELECT level FROM user_upgrades WHERE user_id = ? AND upgrade_id = ?",
            (user_id, upgrade_id)
        )
        return result['level'] if result else 0
    
    async def purchase_upgrade(self, user_id: int, upgrade_id: int) -> bool:
        """Купить/улучшить upgrade"""
        try:
            # Проверяем существующий уровень
            current_level = await self.get_user_upgrade_level(user_id, upgrade_id)
            
            if current_level == 0:
                # Первая покупка
                await self.execute(
                    """INSERT INTO user_upgrades (user_id, upgrade_id, level)
                       VALUES (?, ?, 1)""",
                    (user_id, upgrade_id)
                )
            else:
                # Апгрейд
                await self.execute(
                    """UPDATE user_upgrades 
                       SET level = level + 1
                       WHERE user_id = ? AND upgrade_id = ?""",
                    (user_id, upgrade_id)
                )
            
            return True
        except Exception as e:
            logger.error(f"Error purchasing upgrade: {e}")
            return False
    
    # === ACHIEVEMENTS METHODS ===
    
    async def get_all_achievements(self) -> List[Dict]:
        """Получить все достижения"""
        return await self.fetchall("SELECT * FROM achievements")
    
    async def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Получить достижения пользователя"""
        return await self.fetchall(
            """SELECT ua.*, a.name, a.description, a.icon, a.reward_amount
               FROM user_achievements ua
               JOIN achievements a ON ua.achievement_id = a.id
               WHERE ua.user_id = ?""",
            (user_id,)
        )
    
    async def unlock_achievement(self, user_id: int, achievement_id: int) -> bool:
        """Разблокировать достижение"""
        try:
            await self.execute(
                """INSERT INTO user_achievements (user_id, achievement_id)
                   VALUES (?, ?)""",
                (user_id, achievement_id)
            )
            return True
        except aiosqlite.IntegrityError:
            return False
    
    # === MINIGAMES METHODS ===
    
    async def save_minigame_attempt(self, user_id: int, game_type: str, 
                                    score: int, reward: float):
        """Сохранить попытку мини-игры"""
        await self.execute(
            """INSERT INTO minigame_attempts (user_id, game_type, score, reward)
               VALUES (?, ?, ?, ?)""",
            (user_id, game_type, score, reward)
        )
    
    async def get_user_best_scores(self, user_id: int) -> List[Dict]:
        """Получить лучшие результаты пользователя"""
        return await self.fetchall(
            """SELECT game_type, MAX(score) as best_score, MAX(reward) as best_reward
               FROM minigame_attempts
               WHERE user_id = ?
               GROUP BY game_type""",
            (user_id,)
        )
    
    # === LEADERBOARD METHODS ===
    
    async def get_top_players(self, limit: int = 10) -> List[Dict]:
        """Получить топ игроков по заработку"""
        return await self.fetchall(
            """SELECT u.user_id, u.username, u.first_name, 
                      up.total_earned, up.income_per_hour
               FROM users u
               JOIN user_progress up ON u.user_id = up.user_id
               ORDER BY up.total_earned DESC
               LIMIT ?""",
            (limit,)
        )
    
    async def get_user_rank(self, user_id: int) -> Optional[int]:
        """Получить место пользователя в рейтинге"""
        result = await self.fetchone(
            """SELECT COUNT(*) + 1 as rank
               FROM user_progress
               WHERE total_earned > (
                   SELECT total_earned FROM user_progress WHERE user_id = ?
               )""",
            (user_id,)
        )
        return result['rank'] if result else None


# Singleton экземпляр
db = Database("database/game.db")
