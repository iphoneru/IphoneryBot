from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Chatbot is running!'

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    
    # Simple response logic (replace with your AI logic)
    if 'hello' in user_message.lower():
        bot_response = 'Hi there! How can I help you?'
    elif 'help' in user_message.lower():
        bot_response = 'I can answer questions and chat with you!'
    else:
        bot_response = f'You said: {user_message}'
    
    return jsonify({'response': bot_response})

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
