from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhooks/jivo', methods=['POST'])
def jivo_webhook():
    data = request.json
    print(f"Получен запрос: {data}")

    # Проверяем, что это именно сообщение от клиента
    if data.get('event_name') == 'client_message':
        client_text = data.get('message', {}).get('text', '')
        
        # Формируем ответ для Jivo
        response_data = {
            "result": "ok",
            "commands": [
                {
                    "command": "send_message",
                    "text": f"Привет! Я получил твое сообщение: '{client_text}'. Чем могу помочь?"
                }
            ]
        }
        return jsonify(response_data)

    return jsonify({"result": "ok"})

if __name__ == '__main__':
    app.run(port=10000)
