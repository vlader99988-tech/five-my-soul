from telethon import TelegramClient, events
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import re
from flask import Flask
import threading
import os

app = Flask(__name__)

# ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
api_id = 20382032
api_hash = '5c84aab2e75919ee24d15c15f76419e8'
bot_token = '8551425125:AAEnKEEM6Dk5KdLuJfjHm7IjkQeKvqFivn8'

client = TelegramClient('bot_session', api_id, api_hash)

print("⚡ БОТ ЗАПУСКАЕТСЯ...")

try:
    tokenizer = AutoTokenizer.from_pretrained("sberbank-ai/rugpt3small_based_on_gpt2")
    model = AutoModelForCausalLM.from_pretrained("sberbank-ai/rugpt3small_based_on_gpt2")
    model_loaded = True
    print("✅ МОДЕЛЬ ЗАГРУЖЕНА")
except Exception as e:
    print(f"❌ Ошибка загрузки: {e}")
    model_loaded = False

def generate_short_response(text, user_id):
    if model_loaded:
        try:
            prompt = f"Человек: {text}\nБот:"
            
            inputs = tokenizer.encode(prompt, return_tensors='pt', max_length=128, truncation=True)
            
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
            return generate_quick_response(text)
    else:
        return generate_quick_response(text)

def generate_quick_response(text):
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
        responses = ["Понял", "Ясно", "Интересно", "Хм...", "Ага", "Угу", "Ну", "Да", "Нет", "Ок"]
    
    import random
    return random.choice(responses)

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_private_message(event):
    if not event.out:
        try:
            response = generate_short_response(event.text, event.sender_id)
            await event.reply(response)
            print(f"📨 Личное: {event.text} -> {response}")
        except Exception as e:
            await event.reply("Ок")
            print(f"⚠️ Ошибка: {e}")

@client.on(events.NewMessage(incoming=True, func=lambda e: not e.is_private))
async def handle_group_message(event):
    if not event.out:
        try:
            response = generate_short_response(event.text, event.sender_id)
            await event.reply(response)
            print(f"👥 Группа: {event.text} -> {response}")
        except Exception as e:
            print(f"⚠️ Ошибка в группе: {e}")

def run_bot():
    try:
        client.start(bot_token=bot_token)
        print("=" * 50)
        print("🚀 БОТ УСПЕШНО ЗАПУЩЕН")
        print("✅ Личные сообщения: ВКЛ")
        print("✅ Групповые чаты: ВКЛ")
        print("=" * 50)
        client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")

@app.route('/')
def home():
    return "👻 Бот активен!"

@app.route('/health')
def health():
    return "OK", 200

def start_bot():
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

start_bot()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
