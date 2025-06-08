from flask import Flask, request, jsonify, render_template_string
import logging
from actions.utils.query_router import route_query


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraAI Chat</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f5f5f5;
        }
        .chat-container {
            width: 80%;
            max-width: 800px;
            height: 80vh;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            background-color: white;
            overflow: hidden;
        }
        .chat-header {
            background-color: #4a6fa5;
            color: white;
            padding: 15px 20px;
            font-size: 1.2rem;
            font-weight: bold;
            display: flex;
            align-items: center;
        }
        .chat-header img {
            width: 30px;
            height: 30px;
            margin-right: 10px;
        }
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        .message {
            max-width: 70%;
            padding: 10px 15px;
            margin-bottom: 15px;
            border-radius: 18px;
            line-height: 1.4;
            word-wrap: break-word;
            position: relative;
        }
        .bot-message {
            background-color: #e9eef6;
            color: #333;
            align-self: flex-start;
            border-bottom-left-radius: 5px;
        }
        .user-message {
            background-color: #4a6fa5;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 5px;
        }
        .chat-input {
            display: flex;
            padding: 15px;
            background-color: #f9f9f9;
            border-top: 1px solid #eee;
        }
        .chat-input input {
            flex: 1;
            padding: 12px 15px;
            border: 1px solid #ddd;
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
        }
        .chat-input button {
            background-color: #4a6fa5;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 12px 20px;
            margin-left: 10px;
            cursor: pointer;
            font-size: 1rem;
            transition: background-color 0.3s;
        }
        .chat-input button:hover {
            background-color: #3a5a8f;
        }
        .typing-indicator {
            display: none;
            align-self: flex-start;
            background-color: #e9eef6;
            padding: 10px 15px;
            border-radius: 18px;
            margin-bottom: 15px;
            color: #666;
        }
        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #666;
            border-radius: 50%;
            margin-right: 5px;
            animation: typing 1s infinite;
        }
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
            margin-right: 0;
        }
        @keyframes typing {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }
        pre {
            white-space: pre-wrap;
            margin: 0;
            font-family: inherit;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <img src="https://img.icons8.com/color/48/000000/chat--v1.png" alt="Chat Icon">
            AuraAI™ Assistant
        </div>
        <div class="chat-messages" id="chat-messages">
            <div class="message bot-message">
                Hello! I'm AuraAI™, an intelligent assistant for Outcome-Based Education (OBE). How can I help you today?
            </div>
        </div>
        <div class="typing-indicator" id="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <div class="chat-input">
            <input type="text" id="user-input" placeholder="Type your message here..." autocomplete="off">
            <button id="send-button">Send</button>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const chatMessages = document.getElementById('chat-messages');
            const userInput = document.getElementById('user-input');
            const sendButton = document.getElementById('send-button');
            const typingIndicator = document.getElementById('typing-indicator');

            // Function to add a message to the chat
            function addMessage(message, isUser = false) {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message');
                messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
                
                // Handle newlines and formatting
                const formattedMessage = message.replace(/\\n/g, '<br>');
                messageDiv.innerHTML = `<pre>${formattedMessage}</pre>`;
                
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            // Function to show typing indicator
            function showTypingIndicator() {
                typingIndicator.style.display = 'block';
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            // Function to hide typing indicator
            function hideTypingIndicator() {
                typingIndicator.style.display = 'none';
            }

            // Function to send message to server
            async function sendMessage() {
                const message = userInput.value.trim();
                if (message === '') return;

                // Add user message to chat
                addMessage(message, true);
                userInput.value = '';

                // Show typing indicator
                showTypingIndicator();

                try {
                    // Send message to server
                    const response = await fetch('/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query: message }),
                    });

                    const data = await response.json();
                    
                    // Hide typing indicator
                    hideTypingIndicator();
                    
                    // Add bot response to chat
                    addMessage(data.response);
                } catch (error) {
                    console.error('Error:', error);
                    hideTypingIndicator();
                    addMessage('Sorry, there was an error processing your request.');
                }
            }

            // Event listeners
            sendButton.addEventListener('click', sendMessage);
            userInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // Focus input on load
            userInput.focus();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Render the chat interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/query', methods=['POST'])
def query():
    """Process a query and return the response"""
    data = request.json
    query_text = data.get('query', '')
    
    logger.info(f"Received query: {query_text}")
    
    
    result = route_query(query_text)
    
   
    return jsonify({
        'success': result.get('success', False),
        'response': result.get('message', 'Sorry, I could not process your request.'),
        'query_type': result.get('query_type', 'unknown')
    })

if __name__ == '__main__':
    logger.info("Starting direct endpoint server...")
    app.run(debug=True, port=5005) 