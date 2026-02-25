from flask import Flask, request, jsonify

app = Flask(__name__)

def get_menu_response(text_message):
    return jsonify({
        "result": "ok",
        "commands": [
            {"command": "invite_agent", "agent_id": "bot"},
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

@app.route('/webhooks/jivo', methods=['POST'])
def jivo_webhook():
    data = request.json or {}
    text = data.get('message', {}).get('text', '')

    # Если клиент нажал на цифру или кнопку
    if text in ["1", "Español"]:
        reply = "¡Hola! ¿Cómo puedo ayudarte?"
    elif text in ["2", "Français"]:
        reply = "Bonjour! Comment puis-je vous aider ?"
    elif text in ["3", "Deutsch"]:
        reply = "Hallo! Wie kann ich Ihnen helfen?"
    else:
        # На любой "Hi" или "123" — шлем меню
        return get_menu_response("Welcome! Choose your language / Выберите язык:")

    return jsonify({
        "result": "ok",
        "commands": [{"command": "send_message", "text": reply}]
    })

if __name__ == '__main__':
    app.run(port=10000)
