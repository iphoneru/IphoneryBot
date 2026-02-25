from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhooks/jivo', methods=['POST'])
def jivo_webhook():
    data = request.json
    event = data.get('event_name')
    
    # 1. Срабатывает сразу, как только клиент открыл окно чата
    if event == 'chat_accepted':
        response_data = {
            "result": "ok",
            "commands": [
                {
                    "command": "send_message",
                    "text": "Please choose your language / Пожалуйста, выберите язык:",
                    "buttons": [
                        {"text": "Español"},
                        {"text": "Français"},
                        {"text": "Deutsch"}
                    ]
                }
            ]
        }
        return jsonify(response_data)

    # 2. Срабатывает, когда клиент нажал на кнопку или написал текст
    if event == 'client_message':
        client_text = data.get('message', {}).get('text', '')
        
        # Логика ответов в зависимости от выбора
        if client_text == "Español":
            reply = "¡Hola! ¿Cómo puedo ayudarte?"
        elif client_text == "Français":
            reply = "Bonjour! Comment puis-je vous aider ?"
        elif client_text == "Deutsch":
            reply = "Hallo! Wie kann ich Ihnen helfen?"
        else:
            reply = "I received your message. Please use the buttons above."

        return jsonify({
            "result": "ok",
            "commands": [{"command": "send_message", "text": reply}]
        })

    return jsonify({"result": "ok"})

if __name__ == '__main__':
    app.run(port=10000)
