from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhooks/<provider_id>', methods=['POST'])
def jivo_webhook(provider_id):
    incoming_data = request.json
    print(f"Получен запрос: {incoming_data}")

    reply = {
        "event": "message",
        "message": {
            "text": "Привет! Бот работает. Подключение успешно!"
        }
    }
    return jsonify(reply), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
