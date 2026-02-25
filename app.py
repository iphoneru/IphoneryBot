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
    return "Server is running on Starter plan!"

@app.route('/webhooks/jivo', methods=['POST'])
def jivo_webhook():
    data = request.json or {}
    event = data.get('event_name')
    text = data.get('message', {}).get('text', '') if data.get('message') else ""

    # Если Jivo просто проверяет связь
    if not event:
        return jsonify({"result": "ok"})

    # Если клиент выбрал язык
    if "Español" in text or text == "1":
        reply = "¡Hola! ¿Cómo puedo ayudarte?"
    elif "Français" in text or text == "2":
        reply = "Bonjour! Comment puis-je vous aider ?"
    elif "Deutsch" in text or text == "3":
        reply = "Hallo! Wie kann ich Ihnen helfen?"
    else:
        # На любое другое сообщение — СБРАСЫВАЕМ оператора и шлем меню
        return get_menu_response("Please choose your language:")

    return jsonify({
        "result": "ok",
        "commands": [{"command": "send_message", "text": reply}]
    })

if __name__ == '__main__':
    app.run(port=10000)
