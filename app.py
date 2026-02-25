from flask import Flask, request, jsonify

app = Flask(__name__)

def get_menu_response(text_message):
    return jsonify({
        "result": "ok",
        "commands": [
            {
                "command": "invite_agent",
                "agent_id": "bot" # Сообщаем Jivo, что управляет бот
            },
            {
                "command": "send_message",
                "text": text_message,
                "buttons": [
                    {"text": "Español"},
                    {"text": "Français"},
                    {"text": "Deutsch"}
                ]
            }
        ]
    })

@app.route('/', methods=['GET', 'POST'])
def home():
    return get_menu_response("Welcome! Please choose your language:")

@app.route('/webhooks/jivo', methods=['POST'])
def jivo_webhook():
    data = request.json or {}
    event = data.get('event_name')
    message = data.get('message', {})
    text = message.get('text', '') if isinstance(message, dict) else ""

    # Игнорируем технические сообщения самого бота
    if event == 'bot_message':
        return jsonify({"result": "ok"})

    # Логика ответов
    if "Español" in text:
        reply = "¡Hola! ¿Cómo puedo ayudarte?"
    elif "Français" in text:
        reply = "Bonjour! Comment puis-je vous aider ?"
    elif "Deutsch" in text:
        reply = "Hallo! Wie kann ich Ihnen helfen?"
    else:
        # На любое другое сообщение или старт — принудительно шлем меню
        return get_menu_response("Please choose your language / Выберите язык:")

    return jsonify({
        "result": "ok",
        "commands": [{"command": "send_message", "text": reply}]
    })

if __name__ == '__main__':
    app.run(port=10000)
