"""
Клавиатуры для Telegram бота
"""
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from ..config import settings


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(
            text="🎮 Играть",
            web_app=WebAppInfo(url=settings.WEBAPP_URL)
        )
    )
    builder.row(
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="🏆 Рейтинг")
    )
    builder.row(
        KeyboardButton(text="💰 Собрать доход"),
        KeyboardButton(text="🎯 Достижения")
    )
    builder.row(
        KeyboardButton(text="ℹ️ Помощь")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_stats_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для статистики"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🎮 Открыть игру",
            web_app=WebAppInfo(url=settings.WEBAPP_URL)
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_refresh")
    )
    
    return builder.as_markup()


def get_leaderboard_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для рейтинга"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🌍 Глобальный", callback_data="leaderboard_global"),
        InlineKeyboardButton(text="👥 Группы", callback_data="leaderboard_groups")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="leaderboard_refresh")
    )
    
    return builder.as_markup()


def get_achievements_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура для достижений"""
    builder = InlineKeyboardBuilder()
    
    # Навигация по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"achievements_page_{page-1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(text="🔄", callback_data=f"achievements_page_{page}")
    )
    nav_buttons.append(
        InlineKeyboardButton(text="➡️", callback_data=f"achievements_page_{page+1}")
    )
    
    builder.row(*nav_buttons)
    
    return builder.as_markup()


def get_income_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после сбора дохода"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🎮 Открыть игру",
            web_app=WebAppInfo(url=settings.WEBAPP_URL)
        )
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")
    )
    
    return builder.as_markup()


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура помощи"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🎮 Начать игру",
            web_app=WebAppInfo(url=settings.WEBAPP_URL)
        )
    )
    builder.row(
        InlineKeyboardButton(text="📖 Гайд", callback_data="help_guide"),
        InlineKeyboardButton(text="❓ FAQ", callback_data="help_faq")
    )
    
    return builder.as_markup()
