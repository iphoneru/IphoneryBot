from flask import Flask, request, jsonify

app = Flask(__name__)

# Универсальная функция для ответа кнопками (теперь с 4-й кнопкой для синхронизации)
def get_button_response(text_message):
    return jsonify({
        "result": "ok",
        "commands": [{
            "command": "send_message",
            "text": text_message,
            "buttons": [
                {"text": "Español"},
                {"text": "Français"},
                {"text": "Deutsch"},
                {"text": "Main Menu"}
            ]
        }]
    })

# Обработка корня
@app.route('/', methods=['GET', 'POST'])
def home():
    return get_button_response("Welcome! Please choose your language:")

# Основной путь для Jivo
@app.route('/webhooks/jivo', methods=['GET', 'POST'])
def jivo_webhook():
    if request.method == 'GET':
        return "Server is live!", 200
        
    data = request.json or {}
    event = data.get('event_name')
    
    # Извлекаем текст сообщения
    message = data.get('message', {})
    text = message.get('text', '') if isinstance(message, dict) else ""

    # Если это событие проверки или пустое событие
    if not event or not text:
        return jsonify({"result": "ok"})

    # Логика ответов
    if "Español" in text:
        reply = "¡Hola! ¿Cómo puedo ayudarte con tu iPhone?"
    elif "Français" in text:
        reply = "Bonjour! Comment puis-je vous aider ?"
    elif "Deutsch" in text:
        reply = "Hallo! Wie kann ich Ihnen helfen?"
    elif "Main Menu" in text:
        return get_button_response("Main Menu opened. Please choose your language:")
    else:
        return jsonify({
            "result": "ok",
            "commands": [{"command": "send_message", "text": "Я тебя вижу! Напиши: Español"}]
        })

    return jsonify({
        "result": "ok",
        "commands": [
            {
                "command": "send_message", 
                "text": reply
            }
        ]
    })

if __name__ == '__main__':
    app.run(port=10000)
