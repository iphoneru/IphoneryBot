from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

# HTML template with language buttons
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot</title>
    <style>
        .language-buttons { margin: 20px; }
        .lang-btn { padding: 10px 20px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .chat-container { margin: 20px; }
    </style>
</head>
<body>
    <div class="language-buttons">
        <h3>Select Language / Seleccionar idioma / Choisir la langue / Sprache wählen</h3>
        <button class="lang-btn" onclick="setLanguage('es')">Español</button>
        <button class="lang-btn" onclick="setLanguage('fr')">Français</button>
        <button class="lang-btn" onclick="setLanguage('de')">Deutsch</button>
        <button class="lang-btn" onclick="setLanguage('en')">English</button>
    </div>
    <div class="chat-container" id="chatContainer" style="display:none;">
        <div id="messages"></div>
        <input type="text" id="messageInput" placeholder="Type your message...">
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        let selectedLanguage = '';
        
        function setLanguage(lang) {
            selectedLanguage = lang;
            document.getElementById('chatContainer').style.display = 'block';
            document.querySelector('.language-buttons').style.display = 'none';
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value;
            if (!message) return;
            
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message, language: selectedLanguage})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('messages').innerHTML += 
                    '<div>You: ' + message + '</div><div>Bot: ' + data.response + '</div>';
                input.value = '';
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    language = data.get('language', 'en')
    
    # Language-specific responses
    greetings = {
        'es': '¡Hola! ¿Cómo puedo ayudarte?',
        'fr': 'Bonjour! Comment puis-je vous aider?',
        'de': 'Hallo! Wie kann ich Ihnen helfen?',
        'en': 'Hello! How can I help you?'
    }
    
    if 'hello' in user_message.lower() or 'hola' in user_message.lower():
        bot_response = greetings.get(language, greetings['en'])
    else:
        bot_response = f'You said: {user_message}'
    
    return jsonify({'response': bot_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
