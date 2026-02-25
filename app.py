from flask import Flask, request, jsonify
import os

app = Flask(_name_)

# Твой provider_id от Jivo (обязательно вставь свой!)
PROVIDER_ID = "arb66O7Pbq"  # например: zhFZipzT:8560a55a9af37d68782b3234a84f344c592ab766

# Простая память (для теста; в продакшене используй Redis/DB)
user_languages = {}  # {client_id: 'es' / 'fr' / 'de'}

@app.route(f"/webhooks/{PROVIDER_ID}", methods=["POST"])
def jivo_webhook():
    data = request.json
    print("Получено от Jivo:", data)

    event = data.get("event")
    client_id = data.get("client_id")
    chat_id = data.get("chat_id")
    timestamp = data.get("timestamp", int(time.time()))

    if event == "CLIENT_MESSAGE":
        text = data.get("message", {}).get("text", "").strip().lower()

        # Если это первое сообщение (или нет языка) — отправляем кнопки выбора языка
        if client_id not in user_languages:
            reply = {
                "client_id": client_id,
                "chat_id": chat_id,
                "message": {
                    "type": "BUTTONS",
                    "text": "Please select your language / Por favor selecciona tu idioma / Veuillez sélectionner votre langue",  # fallback текст
                    "title": "Language / Idioma / Langue",
                    "force_reply": True,  # заставляет ответить кнопкой (опционально)
                    "buttons": [
                        {"id": "lang_es", "text": "Español"},
                        {"id": "lang_fr", "text": "Français"},
                        {"id": "lang_de", "text": "Deutsch"}
                    ],
                    "timestamp": timestamp
                }
            }
            return jsonify(reply), 200

        # Если язык уже выбран — отвечаем на нужном языке
        lang = user_languages.get(client_id, 'en')
        reply_text = f"You wrote: {text} (language: {lang})"  # здесь потом подключишь перевод/ИИ

        response = {
            "client_id": client_id,
            "chat_id": chat_id,
            "message": {
                "type": "TEXT",
                "text": reply_text,
                "timestamp": timestamp
            }
        }
        return jsonify(response), 200

    # Обработка клика по кнопке (Jivo пришлёт CLIENT_MESSAGE с text = id кнопки? Нет — пришлёт специальное событие)
    # В документации Jivo: при клике по кнопке приходит CLIENT_MESSAGE с text = id кнопки или текст кнопки
    if event == "CLIENT_MESSAGE" and "lang_" in text:
        lang_code = text.split("_")[1]  # lang_es → es
        user_languages[client_id] = lang_code
        reply_text = f"Язык выбран: {lang_code.upper()}. Чем могу помочь?"
        if lang_code == "es":
            reply_text = "Idioma seleccionado: Español. ¿En qué puedo ayudarte?"
        elif lang_code == "fr":
            reply_text = "Langue sélectionnée : Français. Comment puis-je vous aider ?"
        elif lang_code == "de":
            reply_text = "Sprache ausgewählt: Deutsch. Wie kann ich Ihnen helfen?"

        response = {
            "client_id": client_id,
            "chat_id": chat_id,
            "message": {
                "type": "TEXT",
                "text": reply_text,
                "timestamp": timestamp
            }
        }
        return jsonify(response), 200

    return jsonify({"status": "ok"}), 200

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
