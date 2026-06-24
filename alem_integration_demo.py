"""
FinQuest — Демонстрация интеграции с платформой Alem AI
=========================================================
Этот скрипт показывает, как FinQuest использует 3 инструмента Alem AI:
1. AlemLLM      — персональные финансовые советы
2. Score API    — скоринг финансового поведения  
3. Text-to-Image — генерация облика персонажа

Для запуска: pip install requests && python alem_integration_demo.py
"""

import requests  # Библиотека для HTTP-запросов (интернет-запросов)
import json      # Для работы с JSON-данными
import os        # Для работы с переменными окружения

# ==============================================================
# КОНФИГУРАЦИЯ
# Ключ API берётся из переменных окружения (безопасно!)
# Установи: export ALEM_API_KEY="твой_ключ"
# ==============================================================
API_KEY = os.getenv("ALEM_API_KEY", "demo_key_replace_me")
BASE_URL = "https://api.plus.alem.ai/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ==============================================================
# ТЕСТОВЫЕ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
# В реальном приложении это берётся из базы данных
# ==============================================================
USER_FINANCIAL_DATA = {
    "user_id": "user_42",
    "month": "2025-06",
    "income": 350000,          # тенге
    "expenses": {
        "food": 95000,
        "transport": 28000,
        "entertainment": 45000,
        "utilities": 22000,
        "savings": 50000,
        "other": 30000
    },
    "goals": [
        {"name": "Отпуск", "target": 500000, "saved": 120000},
        {"name": "Машина", "target": 3000000, "saved": 450000}
    ],
    "character_level": 4,
    "character_xp": 780
}


def analyze_with_alemllm(financial_data):
    """
    Инструмент 1: AlemLLM
    Отправляем финансовые данные пользователя и получаем
    персональный совет от языковой модели.
    """
    print("\n🤖 [1/3] Вызов AlemLLM для анализа финансов...")
    
    total_expenses = sum(financial_data["expenses"].values())
    savings_rate = (financial_data["expenses"]["savings"] / financial_data["income"]) * 100
    
    user_message = f"""
    Проанализируй financial ситуацию пользователя и дай 3 конкретных совета:
    
    Доход: {financial_data['income']:,} тг/мес
    Расходы: {total_expenses:,} тг/мес
    Норма сбережений: {savings_rate:.1f}%
    
    Разбивка расходов:
    - Еда: {financial_data['expenses']['food']:,} тг
    - Транспорт: {financial_data['expenses']['transport']:,} тг
    - Развлечения: {financial_data['expenses']['entertainment']:,} тг
    - ЖКХ: {financial_data['expenses']['utilities']:,} тг
    
    Активные цели: {len(financial_data['goals'])} цели
    
    Дай краткий, мотивирующий анализ на русском языке. Максимум 3 предложения.
    """
    
    payload = {
        "model": "alem-llm-latest",
        "messages": [
            {
                "role": "system",
                "content": "Ты — дружелюбный финансовый советник в мобильном приложении. Говоришь кратко, конкретно и мотивирующе."
            },
            {
                "role": "user", 
                "content": user_message
            }
        ],
        "max_tokens": 300,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=HEADERS,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            advice = result["choices"][0]["message"]["content"]
            print(f"   ✅ Совет получен!")
            print(f"   💬 \"{advice[:150]}...\"")
            return {"success": True, "advice": advice}
        else:
            print(f"   ⚠️  API вернул {response.status_code}. Используем демо-ответ.")
            return {
                "success": False,
                "advice": "Отличная работа! Ты откладываешь 14.3% дохода — это выше среднего. "
                          "Попробуй сократить развлечения на 10,000 тг — и цель 'Отпуск' приблизится на 2 месяца. "
                          "Твой персонаж гордится тобой! 🌟"
            }
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка соединения: {e}")
        return {"success": False, "advice": "Демо-режим: советы недоступны офлайн"}


def get_financial_score(financial_data):
    """
    Инструмент 2: Score API
    Отправляем поведенческие данные и получаем скор (0-100),
    который определяет уровень развития персонажа.
    """
    print("\n📊 [2/3] Вызов Score API для оценки финансового поведения...")
    
    total_expenses = sum(financial_data["expenses"].values())
    
    score_payload = {
        "user_id": financial_data["user_id"],
        "period": financial_data["month"],
        "metrics": {
            "income": financial_data["income"],
            "total_expenses": total_expenses,
            "savings_amount": financial_data["expenses"]["savings"],
            "savings_rate": financial_data["expenses"]["savings"] / financial_data["income"],
            "expense_categories": financial_data["expenses"],
            "goals_count": len(financial_data["goals"]),
            "goals_progress": [
                {
                    "name": g["name"],
                    "completion_rate": g["saved"] / g["target"]
                }
                for g in financial_data["goals"]
            ]
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/score",
            headers=HEADERS,
            json=score_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            score = result.get("score", 0)
            print(f"   ✅ Скор получен: {score}/100")
            return {"success": True, "score": score}
        else:
            print(f"   ⚠️  API вернул {response.status_code}. Считаем локально.")
            savings_rate = financial_data["expenses"]["savings"] / financial_data["income"]
            demo_score = min(100, int(savings_rate * 200 + 50))
            print(f"   📈 Демо-скор (локальный расчёт): {demo_score}/100")
            return {"success": False, "score": demo_score}
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка: {e}. Демо-скор: 72")
        return {"success": False, "score": 72}


def generate_character_art(character_level, score):
    """
    Инструмент 3: Text-to-Image
    Генерируем уникальный арт персонажа при достижении нового уровня.
    """
    print("\n🎨 [3/3] Вызов Text-to-Image для генерации персонажа...")
    
    character_prompts = {
        1: "Simple peasant merchant, beginner, coins in hand, friendly expression, RPG style",
        2: "Young trader, modest shop, learning finance, RPG character art",
        3: "Confident merchant, small business owner, money bag, RPG fantasy style",
        4: "Experienced financier, elegant attire, investment charts, RPG art style",
        5: "Master of Finance, golden aura, surrounded by coins and charts, legendary RPG character"
    }
    
    level_key = min(character_level, 5)
    base_prompt = character_prompts.get(level_key, character_prompts[5])
    
    if score >= 80:
        style_addition = "glowing with golden light, very successful"
    elif score >= 60:
        style_addition = "confident, steady progress visible"
    else:
        style_addition = "determined, beginning the journey"
    
    full_prompt = f"{base_prompt}, {style_addition}, clean illustration, no text"
    print(f"   🖼️  Промпт: \"{full_prompt[:80]}...\"")
    
    image_payload = {
        "prompt": full_prompt,
        "negative_prompt": "blurry, low quality, text, watermark, nsfw",
        "width": 512,
        "height": 512,
        "steps": 20,
        "guidance_scale": 7.5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/images/generate",
            headers=HEADERS,
            json=image_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            image_url = result.get("url") or result.get("image_url", "")
            print(f"   ✅ Изображение сгенерировано: {image_url[:60]}...")
            return {"success": True, "image_url": image_url}
        else:
            print(f"   ⚠️  API вернул {response.status_code}. Демо-режим.")
            return {
                "success": False,
                "image_url": f"https://placeholder.com/character_level_{character_level}.png"
            }
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка генерации: {e}")
        return {"success": False, "image_url": "fallback_character.png"}


def calculate_xp_reward(score, previous_score=65):
    base_xp = 50
    if score > previous_score:
        improvement_bonus = (score - previous_score) * 3
    else:
        improvement_bonus = 0
    if score >= 80:
        tier_bonus = 30
    elif score >= 60:
        tier_bonus = 15
    else:
        tier_bonus = 0
    return base_xp + improvement_bonus + tier_bonus


def run_finquest_demo():
    print("=" * 60)
    print("🎮 FinQuest — Демонстрация интеграции Alem AI")
    print("=" * 60)
    
    llm_result = analyze_with_alemllm(USER_FINANCIAL_DATA)
    score_result = get_financial_score(USER_FINANCIAL_DATA)
    current_score = score_result["score"]
    
    xp_earned = calculate_xp_reward(current_score)
    new_xp = USER_FINANCIAL_DATA["character_xp"] + xp_earned
    level_up = new_xp >= (USER_FINANCIAL_DATA["character_level"] * 1000)
    new_level = USER_FINANCIAL_DATA["character_level"] + (1 if level_up else 0)
    
    character_result = None
    if level_up:
        character_result = generate_character_art(new_level, current_score)
    
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ ОТЧЁТ FINQUEST")
    print("=" * 60)
    print(f"\n📊 Финансовый скор: {current_score}/100")
    print(f"🎮 Награда персонажу: +{xp_earned} XP (Уровень: {new_level})")
    print("=" * 60)
    
    return {"score": current_score, "new_level": new_level}


if __name__ == "__main__":
    run_finquest_demo()
