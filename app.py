from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhooks/jivo', methods=['POST'])
def jivo_webhook():
    data = request.json
    event = data.get('event_name')
    
    # Кнопки выбора языка
    language_options = [
        {"text": "Español"},
        {"text": "Français"},
        {"text": "Deutsch"}
    ]

    # Если это новое сообщение от клиента
    if event == 'client_message':
        text = data.get('message', {}).get('text', '')
        
        # Если клиент уже выбрал язык — отвечаем
        if "Español" in text:
            reply = "¡Hola! ¿Cómo puedo ayudarte?"
        elif "Français" in text:
            reply = "Bonjour! Comment puis-je vous aider ?"
        elif "Deutsch" in text:
            reply = "Hallo! Wie kann ich Ihnen helfen?"
        else:
            # Если текст любой другой — снова предлагаем кнопки
            return jsonify({
                "result": "ok",
                "commands": [{
                    "command": "send_message",
                    "text": "Please choose your language:",
                    "buttons": language_options
                }]
            })
        
        return jsonify({
            "result": "ok",
            "commands": [{"command": "send_message", "text": reply}]
        })

    # Для всех остальных событий (включая открытие чата) — шлем кнопки
    return jsonify({
        "result": "ok",
        "commands": [{
            "command": "send_message",
            "text": "Welcome! Please choose your language:",
            "buttons": language_options
        }]
    })

if __name__ == '__main__':
    app.run(port=10000)
