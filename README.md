# Iphonery Jivo Bot

Чат-бот для Jivo на FastAPI + OpenAI GPT-4o-mini. Отвечает на вопросы покупателей iphonery.com, ведёт контекст диалога (20 сообщений в памяти), переводит на оператора через OpenAI function calling.

---

## Структура репозитория

```
.
├── main.py          # FastAPI приложение
├── prompt.txt       # Системный промт для AI (на английском)
├── requirements.txt
├── render.yaml      # Конфиг для деплоя на Render.com
├── .env.example     # Пример переменных окружения
└── README.md
```

---

## Локальный запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/YOUR_USERNAME/iphonery-jivo-bot.git
cd iphonery-jivo-bot

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Создать .env файл
cp .env.example .env
# Отредактировать .env — вставить OPENAI_API_KEY

# 4. Запустить
uvicorn main:app --reload --port 8000
```

Бот будет доступен на `http://localhost:8000/arb66O7Pbq`

---

## Деплой на Render.com

1. Запушить код в GitHub.
2. На Render.com: **New → Web Service → Connect GitHub repo**.
3. В настройках:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. В **Environment Variables** добавить:
   - `OPENAI_API_KEY` = ваш ключ
   - `OPENAI_MODEL` = `gpt-4o-mini` (или `gpt-4o`)
5. После деплоя Render выдаст URL типа `https://iphonery-jivo-bot.onrender.com`

---

## Настройка в Jivo

1. В кабинете Jivo: **Управление → Каналы → Чат-бот**.
2. Указать URL вашего webhook:
   ```
   https://iphonery-jivo-bot.onrender.com/arb66O7Pbq
   ```
3. Токен для аутентификации — указывается в URL (часть `arb66O7Pbq`), либо настраивается в Jivo отдельно.

---

## Как работает

| Событие от Jivo | Действие бота |
|---|---|
| `CLIENT_MESSAGE` | Отправляет текст в OpenAI с историей диалога (20 сообщений), возвращает ответ |
| Функция `transfer_to_agent` вызвана AI | Возвращает `{"event": "ASSIGN_AGENT"}` — Jivo переводит на оператора |
| `CHAT_CLOSED` / `CHAT_FINISHED` | Удаляет историю чата из памяти |

## Контекст диалога

История хранится **в оперативной памяти** (Python dict). При перезапуске сервиса история сбрасывается. Максимум **20 сообщений** на чат (deque с maxlen=20).

---

## Когда бот переводит на оператора

- Клиент явно просит соединить с человеком
- Вопрос об активном заказе (трекинг, статус, проблема с оплатой)
- Клиент недоволен или угрожает жалобой
- Вопрос за пределами знаний бота
- Технический дефект полученного товара
- Оптовые / B2B запросы
- После 2–3 безрезультатных обменов

---

## Health check

```
GET /health → {"status": "ok"}
```
