"""
Игровая логика - расчеты доходов и улучшений
"""
from datetime import datetime, timedelta
from typing import Dict, Tuple
import math

from ..config import settings


class GameEngine:
    """Основная игровая логика"""
    
    @staticmethod
    def calculate_offline_income(
        income_per_hour: float,
        last_collected: datetime,
        max_hours: int = None
    ) -> Tuple[float, float]:
        """
        Рассчитать офлайн доход
        
        Args:
            income_per_hour: Доход в час
            last_collected: Время последнего сбора
            max_hours: Максимум часов офлайн дохода
            
        Returns:
            (income, hours) - доход и количество часов
        """
        if max_hours is None:
            max_hours = settings.OFFLINE_INCOME_MAX_HOURS
        
        now = datetime.now()
        time_passed = now - last_collected
        hours = time_passed.total_seconds() / 3600
        
        # Ограничиваем максимальное время
        hours = min(hours, max_hours)
        
        income = income_per_hour * hours
        
        return income, hours
    
    @staticmethod
    def calculate_upgrade_cost(base_cost: float, current_level: int, 
                              multiplier: float = 1.15) -> float:
        """
        Рассчитать стоимость следующего уровня улучшения
        
        Args:
            base_cost: Базовая стоимость
            current_level: Текущий уровень
            multiplier: Множитель цены за уровень
            
        Returns:
            Стоимость следующего уровня
        """
        return math.ceil(base_cost * (multiplier ** current_level))
    
    @staticmethod
    def calculate_total_income(
        base_income: float,
        upgrades: list
    ) -> Tuple[float, int]:
        """
        Рассчитать общий доход с учетом улучшений
        
        Args:
            base_income: Базовый доход
            upgrades: Список улучшений пользователя
            
        Returns:
            (income_per_hour, guests_per_hour)
        """
        total_income_bonus = 0
        total_guests_bonus = 0
        
        for upgrade in upgrades:
            level = upgrade.get('level', 0)
            income_bonus = upgrade.get('income_bonus', 0)
            guests_bonus = upgrade.get('guests_bonus', 0)
            
            total_income_bonus += income_bonus * level
            total_guests_bonus += guests_bonus * level
        
        income_per_hour = base_income + total_income_bonus
        guests_per_hour = settings.INITIAL_GUESTS_PER_HOUR + total_guests_bonus
        
        return income_per_hour, guests_per_hour
    
    @staticmethod
    def calculate_minigame_reward(score: int, game_type: str) -> float:
        """
        Рассчитать награду за мини-игру
        
        Args:
            score: Набранные очки
            game_type: Тип игры
            
        Returns:
            Сумма награды
        """
        # Базовые множители для разных игр
        multipliers = {
            'burger_flip': 0.5,    # За каждое очко 0.5$
            'speed_tap': 0.3,      # За каждое очко 0.3$
            'memory': 1.0,         # За каждое очко 1$
        }
        
        multiplier = multipliers.get(game_type, 0.5)
        reward = score * multiplier
        
        # Бонус за высокие результаты
        if score > 50:
            reward *= 1.5
        elif score > 100:
            reward *= 2.0
        
        return round(reward, 2)
    
    @staticmethod
    def check_achievement_progress(
        progress_data: Dict,
        achievement: Dict
    ) -> bool:
        """
        Проверить, выполнено ли условие достижения
        
        Args:
            progress_data: Данные прогресса пользователя
            achievement: Данные достижения
            
        Returns:
            True если достижение выполнено
        """
        condition_type = achievement['condition_type']
        condition_value = achievement['condition_value']
        
        if condition_type == 'total_earned':
            return progress_data.get('total_earned', 0) >= condition_value
        
        elif condition_type == 'upgrades_count':
            return progress_data.get('upgrades_count', 0) >= condition_value
        
        elif condition_type == 'guests_served':
            # Рассчитываем общее количество обслуженных гостей
            # На основе времени игры и гостей в час
            # Это упрощенная версия, можно сделать отдельную таблицу
            return False  # TODO: добавить подсчет гостей
        
        return False
    
    @staticmethod
    def format_number(number: float) -> str:
        """
        Форматировать большие числа (1000 -> 1K, 1000000 -> 1M)
        
        Args:
            number: Число для форматирования
            
        Returns:
            Отформатированная строка
        """
        if number < 1000:
            return f"{number:.2f}"
        elif number < 1_000_000:
            return f"{number / 1000:.1f}K"
        elif number < 1_000_000_000:
            return f"{number / 1_000_000:.1f}M"
        else:
            return f"{number / 1_000_000_000:.1f}B"
    
    @staticmethod
    def format_time(hours: float) -> str:
        """
        Форматировать время (часы в читаемый формат)
        
        Args:
            hours: Количество часов
            
        Returns:
            Строка вида "2ч 30м"
        """
        if hours < 1:
            minutes = int(hours * 60)
            return f"{minutes}м"
        
        full_hours = int(hours)
        minutes = int((hours - full_hours) * 60)
        
        if minutes == 0:
            return f"{full_hours}ч"
        
        return f"{full_hours}ч {minutes}м"


# Singleton экземпляр
game_engine = GameEngine()
