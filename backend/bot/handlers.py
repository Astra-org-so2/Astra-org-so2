"""
Обработчики команд бота
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ..database import db
from ..game import game_engine
from .keyboards import (
    get_main_keyboard,
    get_stats_keyboard,
    get_leaderboard_keyboard,
    get_achievements_keyboard,
    get_income_keyboard,
    get_help_keyboard
)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка команды /start"""
    user = message.from_user
    
    # Создаем или получаем пользователя
    existing_user = await db.get_user(user.id)
    
    if not existing_user:
        await db.create_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            language_code=user.language_code or 'ru'
        )
        
        welcome_text = (
            f"🎉 Привет, {user.first_name}!\n\n"
            "Добро пожаловать в игру-симулятор ресторана! 🍔\n\n"
            "🏪 Ты начинаешь с небольшого заведения, которое приносит "
            f"{game_engine.format_number(10)}$/час\n\n"
            "📈 Твоя задача:\n"
            "• Улучшать оборудование\n"
            "• Нанимать персонал\n"
            "• Развивать интерьер\n"
            "• Зарабатывать больше денег\n\n"
            "💡 Доход копится даже когда ты офлайн (до 24 часов)!\n\n"
            "🎮 Нажми кнопку 'Играть' чтобы начать!"
        )
    else:
        await db.update_last_active(user.id)
        welcome_text = (
            f"👋 С возвращением, {user.first_name}!\n\n"
            "Твой бизнес продолжал работать пока тебя не было! 💰\n"
            "Нажми '💰 Собрать доход' чтобы забрать накопленные деньги."
        )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    """Показать статистику пользователя"""
    user_id = message.from_user.id
    await db.update_last_active(user_id)
    
    progress = await db.get_user_progress(user_id)
    if not progress:
        await message.answer("❌ Данные не найдены. Используй /start")
        return
    
    upgrades = await db.get_user_upgrades(user_id)
    upgrades_count = len([u for u in upgrades if u['level'] > 0])
    
    # Рассчитываем офлайн доход
    last_collected = datetime.fromisoformat(progress['last_income_collected'])
    offline_income, hours = game_engine.calculate_offline_income(
        progress['income_per_hour'],
        last_collected
    )
    
    stats_text = (
        f"📊 <b>Твоя статистика</b>\n\n"
        f"💰 Баланс: <b>{game_engine.format_number(progress['balance'])}$</b>\n"
        f"📈 Доход: <b>{game_engine.format_number(progress['income_per_hour'])}$/час</b>\n"
        f"👥 Гости: <b>{progress['guests_per_hour']} в час</b>\n"
        f"💎 Всего заработано: <b>{game_engine.format_number(progress['total_earned'])}$</b>\n\n"
        f"🔧 Куплено улучшений: <b>{upgrades_count}</b>\n\n"
        f"⏰ Накоплено за {game_engine.format_time(hours)}: "
        f"<b>{game_engine.format_number(offline_income)}$</b>\n"
        f"└ Используй '💰 Собрать доход' чтобы забрать!"
    )
    
    await message.answer(
        stats_text,
        parse_mode="HTML",
        reply_markup=get_stats_keyboard(user_id)
    )


@router.message(F.text == "💰 Собрать доход")
async def collect_income(message: Message):
    """Собрать накопленный доход"""
    user_id = message.from_user.id
    await db.update_last_active(user_id)
    
    progress = await db.get_user_progress(user_id)
    if not progress:
        await message.answer("❌ Данные не найдены. Используй /start")
        return
    
    # Рассчитываем доход
    last_collected = datetime.fromisoformat(progress['last_income_collected'])
    income, hours = game_engine.calculate_offline_income(
        progress['income_per_hour'],
        last_collected
    )
    
    if income < 0.01:
        await message.answer(
            "⏰ Пока нечего собирать!\n"
            "Подожди немного, твой бизнес работает... 🏪"
        )
        return
    
    # Добавляем доход
    await db.update_balance(user_id, income, update_total=True)
    await db.update_last_income_collected(user_id)
    
    # Получаем новый баланс
    new_progress = await db.get_user_progress(user_id)
    
    income_text = (
        f"💰 <b>Доход собран!</b>\n\n"
        f"📦 Получено: <b>+{game_engine.format_number(income)}$</b>\n"
        f"⏰ За {game_engine.format_time(hours)}\n\n"
        f"💼 Новый баланс: <b>{game_engine.format_number(new_progress['balance'])}$</b>\n\n"
        f"📈 Текущий доход: <b>{game_engine.format_number(progress['income_per_hour'])}$/час</b>"
    )
    
    await message.answer(
        income_text,
        parse_mode="HTML",
        reply_markup=get_income_keyboard()
    )


@router.message(F.text == "🏆 Рейтинг")
async def show_leaderboard(message: Message):
    """Показать рейтинг игроков"""
    user_id = message.from_user.id
    await db.update_last_active(user_id)
    
    top_players = await db.get_top_players(10)
    user_rank = await db.get_user_rank(user_id)
    
    leaderboard_text = "🏆 <b>Топ игроков</b>\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    for idx, player in enumerate(top_players):
        rank = idx + 1
        medal = medals[idx] if idx < 3 else f"{rank}."
        
        name = player['first_name'] or player['username'] or f"User {player['user_id']}"
        earnings = game_engine.format_number(player['total_earned'])
        
        # Выделяем текущего пользователя
        if player['user_id'] == user_id:
            leaderboard_text += f"<b>➤ {medal} {name}: {earnings}$</b>\n"
        else:
            leaderboard_text += f"{medal} {name}: {earnings}$\n"
    
    if user_rank and user_rank > 10:
        leaderboard_text += f"\n...\n📍 Твоё место: <b>{user_rank}</b>"
    
    await message.answer(
        leaderboard_text,
        parse_mode="HTML",
        reply_markup=get_leaderboard_keyboard()
    )


@router.message(F.text == "🎯 Достижения")
async def show_achievements(message: Message):
    """Показать достижения"""
    user_id = message.from_user.id
    await db.update_last_active(user_id)
    
    all_achievements = await db.get_all_achievements()
    user_achievements = await db.get_user_achievements(user_id)
    
    unlocked_ids = {a['achievement_id'] for a in user_achievements}
    
    achievements_text = "🎯 <b>Достижения</b>\n\n"
    
    unlocked_count = len(unlocked_ids)
    total_count = len(all_achievements)
    
    achievements_text += f"📊 Получено: {unlocked_count}/{total_count}\n\n"
    
    for achievement in all_achievements[:10]:  # Первые 10
        icon = achievement.get('icon', '🏅')
        name = achievement['name']
        description = achievement['description']
        
        if achievement['id'] in unlocked_ids:
            achievements_text += f"✅ {icon} <b>{name}</b>\n   {description}\n\n"
        else:
            achievements_text += f"🔒 {icon} {name}\n   {description}\n\n"
    
    await message.answer(
        achievements_text,
        parse_mode="HTML",
        reply_markup=get_achievements_keyboard()
    )


@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    """Показать помощь"""
    help_text = (
        "ℹ️ <b>Как играть</b>\n\n"
        "🎮 <b>Основы:</b>\n"
        "• Твой ресторан приносит доход каждый час\n"
        "• Доход копится даже офлайн (до 24 часов)\n"
        "• Собирай деньги кнопкой '💰 Собрать доход'\n\n"
        "🔧 <b>Улучшения:</b>\n"
        "• Оборудование - увеличивает доход\n"
        "• Персонал - приносит бонусы\n"
        "• Интерьер - привлекает гостей\n\n"
        "🎯 <b>Мини-игры:</b>\n"
        "• Играй в мини-игры для бонусов\n"
        "• Зарабатывай дополнительные деньги\n\n"
        "🏆 <b>Достижения:</b>\n"
        "• Выполняй условия для наград\n"
        "• Получай бонусы за достижения\n\n"
        "💡 <b>Совет:</b> Регулярно заходи и улучшай бизнес!"
    )
    
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=get_help_keyboard()
    )


# Callback handlers
@router.callback_query(F.data == "stats_refresh")
async def refresh_stats(callback: CallbackQuery):
    """Обновить статистику"""
    await callback.answer("🔄 Обновляю...")
    await show_stats(callback.message)


@router.callback_query(F.data == "show_stats")
async def callback_show_stats(callback: CallbackQuery):
    """Показать статистику из callback"""
    await callback.answer()
    await show_stats(callback.message)


@router.callback_query(F.data.startswith("leaderboard_"))
async def leaderboard_callback(callback: CallbackQuery):
    """Обработка callbacks рейтинга"""
    await callback.answer("🔄 Обновляю...")
    await show_leaderboard(callback.message)


@router.callback_query(F.data.startswith("achievements_page_"))
async def achievements_page(callback: CallbackQuery):
    """Переключение страниц достижений"""
    await callback.answer()
    await show_achievements(callback.message)
