// EduTrack Pro - AI Chatbot Assistant Javascript

document.addEventListener('DOMContentLoaded', () => {
    const chatbotFab = document.getElementById('chatbotFab');
    const chatbotWidget = document.getElementById('chatbotWidget');
    const chatbotClose = document.getElementById('chatbotClose');
    const chatbotSend = document.getElementById('chatbotSend');
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotBody = document.getElementById('chatbotBody');

    if (!chatbotFab || !chatbotWidget) return;

    // Toggle widget active state
    chatbotFab.addEventListener('click', () => {
        chatbotWidget.classList.toggle('active');
        if (chatbotWidget.classList.contains('active')) {
            chatbotInput.focus();
        }
    });

    chatbotClose.addEventListener('click', () => {
        chatbotWidget.classList.remove('active');
    });

    // Helper to extract CSRF token from meta tag or DOM forms
    const getCsrfToken = () => {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.getAttribute('content');
        const input = document.querySelector('input[name="csrf_token"]');
        return input ? input.value : '';
    };

    const appendMessage = (sender, text) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message');
        
        if (sender === 'bot') {
            messageDiv.classList.add('bot-message');
            messageDiv.innerHTML = `
                <i class="fas fa-robot bot-icon"></i>
                <div class="message-bubble">${text}</div>
            `;
        } else {
            messageDiv.classList.add('user-message');
            messageDiv.innerHTML = `
                <div class="message-bubble">${text}</div>
            `;
        }
        
        chatbotBody.appendChild(messageDiv);
        chatbotBody.scrollTop = chatbotBody.scrollHeight;
    };

    const sendMessage = () => {
        const message = chatbotInput.value.trim();
        if (!message) return;

        // Display user message
        appendMessage('user', message);
        chatbotInput.value = '';

        // Display typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('chat-message', 'bot-message', 'typing-indicator-msg');
        typingDiv.innerHTML = `
            <i class="fas fa-robot bot-icon"></i>
            <div class="message-bubble"><i class="fas fa-ellipsis-h fa-sm fa-pulse"></i> Thinking...</div>
        `;
        chatbotBody.appendChild(typingDiv);
        chatbotBody.scrollTop = chatbotBody.scrollHeight;

        // POST request to backend chatbot route
        fetch('/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ message: message })
        })
        .then(res => res.json())
        .then(data => {
            // Remove typing indicator
            const indicator = chatbotBody.querySelector('.typing-indicator-msg');
            if (indicator) indicator.remove();

            // Display bot response
            appendMessage('bot', data.response || "Sorry, I encountered an issue. Let's try again.");
        })
        .catch(err => {
            const indicator = chatbotBody.querySelector('.typing-indicator-msg');
            if (indicator) indicator.remove();
            appendMessage('bot', "Connection error. Please check if the server is running.");
        });
    };

    chatbotSend.addEventListener('click', sendMessage);
    chatbotInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
