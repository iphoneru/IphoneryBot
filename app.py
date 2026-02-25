from flask import Flask, request, jsonify

app = Flask(__name__)

def get_menu_response(text_message):
    return jsonify({
        "result": "ok",
        "commands": [
            {
                "command": "invite_agent",
                "agent_id": "bot"
            },
            {
                "command": "send_message",
                "text": f"{text_message}\n\n1. Español\n2. Français\n3. Deutsch",
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
    return get_menu_response("Welcome! Choose your language / Выберите язык:")

@app.route('/webhooks/jivo', methods=['POST'])
def jivo_webhook():
    data = request.json or {}
    text = data.get('message', {}).get('text', '')

    # Логика выбора
    if "Español" in text or text == "1":
        reply = "¡Hola! ¿Cómo puedo ayudarte con tu iPhone?"
    elif "Français" in text or text == "2":
        reply = "Bonjour! Comment puis-je vous aider ?"
    elif "Deutsch" in text or text == "3":
        reply = "Hallo! Wie kann ich Ihnen helfen?"
    else:
        # На любое другое сообщение — кидаем меню
        return get_menu_response("Please choose / Выберите:")

    return jsonify({
        "result": "ok",
        "commands": [{"command": "send_message", "text": reply}]
    })

if __name__ == '__main__':
    app.run(port=10000)
