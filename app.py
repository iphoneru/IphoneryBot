from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhooks/jivo', methods=['POST'])
def jivo_webhook():
    data = request.json
    event = data.get('event_name')
    
    # 1. Срабатывает сразу при открытии чата
    if event == 'chat_accepted':
        return jsonify({
            "result": "ok",
            "commands": [
                {
                    "command": "set_agent_info",
                    "name": "Iphonery Assistant",
                    "title": "AI Bot"
                },
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
        })

    # 2. Обработка выбора (кликов по кнопкам)
    if event == 'client_message':
        return jsonify({
            "result": "ok",
            "commands": [
                {
                    "command": "send_message",
                    "text": "Please choose your language:",
                    "buttons": [
                        {"text": "Español"},
                        {"text": "Français"},
                        {"text": "Deutsch"}
                    ]
                }
            ]
        })

    return jsonify({"result": "ok"})

if __name__ == '__main__':
    app.run(port=10000)
