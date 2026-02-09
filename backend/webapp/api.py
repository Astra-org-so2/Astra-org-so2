"""
API для Web App
"""
from aiohttp import web
from datetime import datetime
import json
import logging

from ..database import db
from ..game import game_engine
from ..config import settings

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()


@routes.get('/api/health')
async def health_check(request):
    """Проверка здоровья API"""
    return web.json_response({'status': 'ok'})


@routes.get('/api/user/{user_id}/profile')
async def get_user_profile(request):
    """Получить профиль пользователя"""
    user_id = int(request.match_info['user_id'])
    
    user = await db.get_user(user_id)
    progress = await db.get_user_progress(user_id)
    
    if not user or not progress:
        return web.json_response(
            {'error': 'User not found'},
            status=404
        )
    
    # Рассчитываем офлайн доход
    last_collected = datetime.fromisoformat(progress['last_income_collected'])
    offline_income, hours = game_engine.calculate_offline_income(
        progress['income_per_hour'],
        last_collected
    )
    
    return web.json_response({
        'user': {
            'id': user['user_id'],
            'username': user['username'],
            'first_name': user['first_name']
        },
        'progress': {
            'balance': progress['balance'],
            'income_per_hour': progress['income_per_hour'],
            'guests_per_hour': progress['guests_per_hour'],
            'total_earned': progress['total_earned'],
            'offline_income': offline_income,
            'offline_hours': hours
        }
    })


@routes.post('/api/user/{user_id}/collect-income')
async def collect_income(request):
    """Собрать накопленный доход"""
    user_id = int(request.match_info['user_id'])
    
    progress = await db.get_user_progress(user_id)
    if not progress:
        return web.json_response(
            {'error': 'User not found'},
            status=404
        )
    
    # Рассчитываем доход
    last_collected = datetime.fromisoformat(progress['last_income_collected'])
    income, hours = game_engine.calculate_offline_income(
        progress['income_per_hour'],
        last_collected
    )
    
    if income < 0.01:
        return web.json_response({
            'collected': 0,
            'message': 'No income to collect yet'
        })
    
    # Добавляем доход
    await db.update_balance(user_id, income, update_total=True)
    await db.update_last_income_collected(user_id)
    
    # Получаем новый баланс
    new_progress = await db.get_user_progress(user_id)
    
    return web.json_response({
        'collected': income,
        'hours': hours,
        'new_balance': new_progress['balance'],
        'total_earned': new_progress['total_earned']
    })


@routes.get('/api/upgrades')
async def get_all_upgrades(request):
    """Получить все доступные улучшения"""
    upgrades = await db.get_all_upgrades()
    
    return web.json_response({
        'upgrades': upgrades
    })


@routes.get('/api/user/{user_id}/upgrades')
async def get_user_upgrades(request):
    """Получить улучшения пользователя"""
    user_id = int(request.match_info['user_id'])
    
    user_upgrades = await db.get_user_upgrades(user_id)
    all_upgrades = await db.get_all_upgrades()
    
    # Объединяем данные
    upgrades_with_levels = []
    for upgrade in all_upgrades:
        user_upgrade = next(
            (u for u in user_upgrades if u['upgrade_id'] == upgrade['id']),
            None
        )
        
        current_level = user_upgrade['level'] if user_upgrade else 0
        next_cost = game_engine.calculate_upgrade_cost(
            upgrade['base_cost'],
            current_level,
            upgrade['cost_multiplier']
        )
        
        upgrades_with_levels.append({
            **upgrade,
            'current_level': current_level,
            'next_cost': next_cost
        })
    
    return web.json_response({
        'upgrades': upgrades_with_levels
    })


@routes.post('/api/user/{user_id}/purchase-upgrade')
async def purchase_upgrade(request):
    """Купить улучшение"""
    user_id = int(request.match_info['user_id'])
    data = await request.json()
    
    upgrade_id = data.get('upgrade_id')
    if not upgrade_id:
        return web.json_response(
            {'error': 'upgrade_id is required'},
            status=400
        )
    
    # Получаем данные
    progress = await db.get_user_progress(user_id)
    upgrade = await db.fetchone(
        "SELECT * FROM upgrades WHERE id = ?",
        (upgrade_id,)
    )
    
    if not upgrade:
        return web.json_response(
            {'error': 'Upgrade not found'},
            status=404
        )
    
    # Получаем текущий уровень
    current_level = await db.get_user_upgrade_level(user_id, upgrade_id)
    
    # Рассчитываем стоимость
    cost = game_engine.calculate_upgrade_cost(
        upgrade['base_cost'],
        current_level,
        upgrade['cost_multiplier']
    )
    
    # Проверяем баланс
    if progress['balance'] < cost:
        return web.json_response(
            {'error': 'Insufficient balance'},
            status=400
        )
    
    # Покупаем
    await db.purchase_upgrade(user_id, upgrade_id)
    await db.update_balance(user_id, -cost, update_total=False)
    
    # Пересчитываем доход
    user_upgrades = await db.get_user_upgrades(user_id)
    new_income, new_guests = game_engine.calculate_total_income(
        settings.INITIAL_INCOME_PER_HOUR,
        user_upgrades
    )
    
    await db.update_income_stats(user_id, new_income, new_guests)
    
    # Получаем обновленные данные
    new_progress = await db.get_user_progress(user_id)
    
    return web.json_response({
        'success': True,
        'purchased': {
            'upgrade_id': upgrade_id,
            'name': upgrade['name'],
            'new_level': current_level + 1,
            'cost': cost
        },
        'new_balance': new_progress['balance'],
        'new_income_per_hour': new_progress['income_per_hour'],
        'new_guests_per_hour': new_progress['guests_per_hour']
    })


@routes.get('/api/user/{user_id}/achievements')
async def get_user_achievements(request):
    """Получить достижения пользователя"""
    user_id = int(request.match_info['user_id'])
    
    all_achievements = await db.get_all_achievements()
    user_achievements = await db.get_user_achievements(user_id)
    
    unlocked_ids = {a['achievement_id'] for a in user_achievements}
    
    # Получаем прогресс для проверки
    progress = await db.get_user_progress(user_id)
    upgrades = await db.get_user_upgrades(user_id)
    
    progress_data = {
        'total_earned': progress['total_earned'],
        'upgrades_count': len([u for u in upgrades if u['level'] > 0])
    }
    
    achievements_with_status = []
    for achievement in all_achievements:
        is_unlocked = achievement['id'] in unlocked_ids
        can_unlock = game_engine.check_achievement_progress(
            progress_data,
            achievement
        ) and not is_unlocked
        
        achievements_with_status.append({
            **achievement,
            'unlocked': is_unlocked,
            'can_unlock': can_unlock
        })
    
    return web.json_response({
        'achievements': achievements_with_status,
        'unlocked_count': len(unlocked_ids),
        'total_count': len(all_achievements)
    })


@routes.post('/api/user/{user_id}/minigame-result')
async def save_minigame_result(request):
    """Сохранить результат мини-игры"""
    user_id = int(request.match_info['user_id'])
    data = await request.json()
    
    game_type = data.get('game_type')
    score = data.get('score', 0)
    
    if not game_type:
        return web.json_response(
            {'error': 'game_type is required'},
            status=400
        )
    
    # Рассчитываем награду
    reward = game_engine.calculate_minigame_reward(score, game_type)
    
    # Сохраняем результат
    await db.save_minigame_attempt(user_id, game_type, score, reward)
    
    # Добавляем награду
    await db.update_balance(user_id, reward, update_total=True)
    
    # Получаем новый баланс
    progress = await db.get_user_progress(user_id)
    
    return web.json_response({
        'score': score,
        'reward': reward,
        'new_balance': progress['balance']
    })


@routes.get('/api/leaderboard')
async def get_leaderboard(request):
    """Получить таблицу лидеров"""
    limit = int(request.query.get('limit', 10))
    
    top_players = await db.get_top_players(limit)
    
    return web.json_response({
        'leaderboard': top_players
    })


@routes.get('/api/user/{user_id}/rank')
async def get_user_rank(request):
    """Получить место пользователя в рейтинге"""
    user_id = int(request.match_info['user_id'])
    
    rank = await db.get_user_rank(user_id)
    
    return web.json_response({
        'rank': rank
    })


# CORS middleware
@web.middleware
async def cors_middleware(request, handler):
    """CORS middleware для разработки"""
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response


def create_app():
    """Создать aiohttp приложение"""
    app = web.Application(middlewares=[cors_middleware])
    app.add_routes(routes)
    
    # Serve static files для Web App
    app.router.add_static('/static/', path='../frontend/dist', name='static')
    
    return app
