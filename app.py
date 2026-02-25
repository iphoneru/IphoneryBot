from flask import Flask, request, jsonify

app = Flask(__name__)

# Универсальная функция для ответа кнопками
def get_button_response(text_message):
    return jsonify({
        "result": "ok",
        "commands": [{
            "command": "send_message",
            "text": text_message,
            "buttons": [
                {"text": "Español"},
                {"text": "Français"},
                {"text": "Deutsch"}
            ]
        }]
    })

# Обработка корня (чтобы не было 404)
@app.route('/', methods=['GET', 'POST'])
def home():
    return get_button_response("Welcome! Please choose your language:")

# Твой основной путь
@app.route('/webhooks/jivo', methods=['GET', 'POST'])
def jivo_webhook():
    if request.method == 'GET':
        return "Server is live!", 200
        
    data = request.json or {}
    event = data.get('event_name')
    text = data.get('message', {}).get('text', '')

    # Если нажат конкретный язык
    if "Español" in text:
        reply = "¡Hola! ¿Cómo puedo ayudarte?"
    elif "Français" in text:
        reply = "Bonjour! Comment puis-je vous aider ?"
    elif "Deutsch" in text:
        reply = "Hallo! Wie kann ich Ihnen helfen?"
    else:
        # На любое другое сообщение — кидаем кнопки
        return get_button_response("Please choose your language:")

    return jsonify({
        "result": "ok",
        "commands": [{"command": "send_message", "text": reply}]
    })

if __name__ == '__main__':
    app.run(port=10000)
