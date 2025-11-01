import subprocess
import sys

# Автоматическая установка зависимостей
def install_packages():
    packages = ['flask', 'telethon', 'transformers', 'torch']
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"📦 Установка {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_packages()

from flask import Flask
from threading import Thread
import os
from telethon import TelegramClient, events
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import re

# Инициализация Flask приложения для поддержания активности
app = Flask('')

@app.route('/')
def home():
    return "🤖 Бот активен и работает!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# Запуск веб-сервера в отдельном потоке
Thread(target=run_web).start()

# ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
api_id = 20382032
api_hash = '5c84aab2e75919ee24d15c15f76419e8'
bot_token = os.environ.get('BOT_TOKEN', '8551425125:AAEnKEEM6Dk5KdLuJfjHm7IjkQeKvqFivn8')

# Инициализация клиента
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

print("⚡ ЗАГРУЗКА БОТА ДЛЯ ЧАТОВ...")
print("🌐 Веб-сервер запущен для поддержания активности")

try:
    tokenizer = AutoTokenizer.from_pretrained("sberbank-ai/rugpt3small_based_on_gpt2")
    model = AutoModelForCausalLM.from_pretrained("sberbank-ai/rugpt3mall_based_on_gpt2")
    model_loaded = True
    print("✅ МОДЕЛЬ ЗАГРУЖЕНА")
except Exception as e:
    print(f"❌ Ошибка загрузки модели: {e}")
    model_loaded = False

def generate_short_response(text, user_id):
    """Короткие ответы для чатов"""
    
    if model_loaded:
        try:
            prompt = f"Человек: {text}\nБот:"
            
            inputs = tokenizer.encode(
                prompt, 
                return_tensors='pt', 
                max_length=128, 
                truncation=True
            )
            
            with torch.no_grad():
                response_ids = model.generate(
                    inputs,
                    max_new_tokens=40,
                    do_sample=True,
                    temperature=0.9,
                    top_k=30,
                    top_p=0.85,
                    repetition_penalty=1.1,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            generated_tokens = response_ids[0][inputs.shape[1]:]
            response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            # Обрезаем до первого предложения
            for end_marker in ['.', '!', '?', '\n']:
                if end_marker in response:
                    response = response.split(end_marker)[0] + end_marker
                    break
            
            if len(response) > 80:
                response = response[:80].strip()
            
            if not response or len(response) < 2:
                response = generate_quick_response(text)
            
            return response.strip()
            
        except Exception as e:
            print(f"❌ Ошибка генерации: {e}")
            return generate_quick_response(text)
    else:
        return generate_quick_response(text)

def generate_quick_response(text):
    """Быстрые ответы для чатов"""
    
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['привет', 'хай', 'hello', 'здравств']):
        responses = ["Привет!", "Здаров!", "Хай!", "Приветствую"]
    
    elif any(word in text_lower for word in ['как дела', 'как ты']):
        responses = ["Норм", "Отлично", "Все ок", "Хорошо"]
    
    elif any(word in text_lower for word in ['пока', 'до свидан']):
        responses = ["Пока!", "До встречи", "Бывай", "Увидимся"]
    
    elif any(word in text_lower for word in ['что', 'как', 'почему']):
        responses = ["Не знаю", "Интересно", "Хм...", "Спроси еще"]
    
    else:
        responses = [
            "Понял", "Ясно", "Интересно", "Хм...", "Ага", 
            "Угу", "Ну", "Да", "Нет", "Ок", "Лол", "Кек"
        ]
    
    import random
    return random.choice(responses)

# Обработчик для ЛИЧНЫХ сообщений
@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_private_message(event):
    if not event.out:
        user_id = event.sender_id
        user_message = event.text
        
        print(f"📨 ЛИЧНОЕ от {user_id}: {user_message}")
        
        try:
            response = generate_short_response(user_message, user_id)
            await event.reply(response)
            print(f"✅ ОТВЕТ: {response}")
        except Exception as e:
            await event.reply("Ок")
            print(f"⚠️ {e}")

# Обработчик для ГРУППОВЫХ чатов
@client.on(events.NewMessage(incoming=True, func=lambda e: not e.is_private))
async def handle_group_message(event):
    if not event.out:
        chat_id = event.chat_id
        user_id = event.sender_id
        user_message = event.text
        
        # Отвечаем только если бота упомянули или это ответ на его сообщение
        me = await client.get_me()
        if f'@{me.username}' in user_message or event.is_reply:
            print(f"👥 ГРУППА {chat_id} от {user_id}: {user_message}")
            
            try:
                response = generate_short_response(user_message, user_id)
                await event.reply(response)
                print(f"✅ ОТВЕТ В ГРУППЕ: {response}")
            except Exception as e:
                print(f"⚠️ Ошибка в группе: {e}")

print("=" * 50)
print("🚀 БОТ ЗАПУЩЕН ДЛЯ ЧАТОВ")
print("✅ ЛИЧНЫЕ СООБЩЕНИЯ: ВКЛ")
print("✅ ГРУППОВЫЕ ЧАТЫ: ВКЛ (только при упоминании)")
print("🌐 ВЕБ-СЕРВЕР: АКТИВЕН")
print("=" * 50)

client.run_until_disconnected()
