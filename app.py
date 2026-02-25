from flask import Flask, request, jsonify
import os
import time

app = Flask(__name__)

# ВАЖНО: Замени на свой реальный ID из настроек Jivo (раздел Интеграция для разработчиков)
# Если оставить этот, запросы от Jivo не дойдут до функции
PROVIDER_ID = "arb66O7Pbq" 

# Простая память для хранения выбора языка
user_languages = {}  # {client_id: 'es' / 'fr' / 'de'}

@app.route("/", methods=["GET"])
def index():
    return "Бот работает! Ожидаю вебхуки от Jivo.", 200

@app.route(f"/webhooks/{PROVIDER_ID}", methods=["POST"])
def jivo_webhook():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data"}), 400

    print("Получено от Jivo:", data)

    event = data.get("event")
    client_id = data.get("client_id")
    chat_id = data.get("chat_id")
    # Используем текущее время, если Jivo не прислал timestamp
    timestamp = data.get("timestamp", int(time.time()))

    if event == "CLIENT_MESSAGE":
        message_data = data.get("message", {})
        text = message_data.get("text", "").strip()
        
        # 1. Проверяем, не нажал ли пользователь на кнопку выбора языка
        if text == "lang_es" or text == "Español":
            user_languages[client_id] = "es"
            return send_text_reply(client_id, chat_id, "Idioma seleccionado: Español. ¿En qué puedo ayudarte?", timestamp)
        
        elif text == "lang_fr" or text == "Français":
            user_languages[client_id] = "fr"
            return send_text_reply(client_id, chat_id, "Langue sélectionnée : Français. Comment puis-je vous aider ?", timestamp)
        
        elif text == "lang_de" or text == "Deutsch":
            user_languages[client_id] = "de"
            return send_text_reply(client_id, chat_id, "Sprache ausgewählt: Deutsch. Wie kann ich Ihnen helfen?", timestamp)

        # 2. Если язык еще не выбран — отправляем кнопки
        if client_id not in user_languages:
            reply = {
                "client_id": client_id,
                "chat_id": chat_id,
                "message": {
                    "type": "BUTTONS",
                    "text": "Please select your language / Пожалуйста, выберите язык:",
                    "title": "Language / Idioma / Langue",
                    "buttons": [
                        {"id": "lang_es", "text": "Español"},
                        {"text": "Français"}, # Можно отправлять без ID, тогда в text придет название
                        {"id": "lang_de", "text": "Deutsch"}
                    ],
                    "timestamp": timestamp
                }
            }
            return jsonify(reply), 200

        # 3. Если язык выбран — отвечаем в зависимости от контекста
        lang = user_languages.get(client_id)
        reply_text = f"Я получил ваше сообщение: '{text}'. (Выбранный язык: {lang})"
        return send_text_reply(client_id, chat_id, reply_text, timestamp)

    return jsonify({"status": "ok"}), 200

def send_text_reply(client_id, chat_id, text, timestamp):
    """Вспомогательная функция для отправки текстовых ответов"""
    response = {
        "client_id": client_id,
        "chat_id": chat_id,
        "message": {
            "type": "TEXT",
            "text": text,
            "timestamp": timestamp
        }
    }
    return jsonify(response), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
