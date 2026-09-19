/**
 * FinMate — Chatbot logic and UI controller.
 * Manages conversational interactions, suggested prompts, and live data updates.
 */

const Chat = {
  messagesContainer: null,
  inputElement: null,
  sendButton: null,
  welcomeElement: null,
  isWaitingResponse: false,

  init() {
    this.messagesContainer = document.getElementById('chat-messages');
    this.inputElement = document.getElementById('chat-input');
    this.sendButton = document.getElementById('chat-send-btn');
    this.welcomeElement = document.getElementById('chat-welcome');

    if (!this.inputElement || !this.sendButton) return;

    // Send button event
    this.sendButton.addEventListener('click', () => this.sendMessage());

    // Enter key event (Shift+Enter for newline)
    this.inputElement.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Auto-resize textarea
    this.inputElement.addEventListener('input', () => {
      this.inputElement.style.height = 'auto';
      this.inputElement.style.height = Math.min(this.inputElement.scrollHeight, 120) + 'px';
    });
  },

  /**
   * Send a user message to the AI assistant
   */
  async sendMessage(customText = null) {
    const text = (customText !== null ? customText : this.inputElement.value).trim();
    if (!text || this.isWaitingResponse) return;

    // Hide welcome on first user message
    if (this.welcomeElement) {
      this.welcomeElement.style.display = 'none';
    }

    // Append user message
    this.appendMessage('user', text);

    // Reset input
    if (customText === null) {
      this.inputElement.value = '';
      this.inputElement.style.height = 'auto';
    }

    // Show loading indicator
    this.isWaitingResponse = true;
    this.sendButton.disabled = true;
    const typingId = this.showTypingIndicator();

    try {
      const response = await Api.sendChatMessage(text);
      this.removeTypingIndicator(typingId);

      // Append assistant reply
      this.appendMessage('assistant', response.reply);

      // If an action was taken (e.g. transaction added), notify and refresh dashboard
      if (response.action_taken === 'transaction_added') {
        const txn = response.data;
        const msg = txn ? `Added: ¥${txn.amount} (${txn.category})` : 'Transaction recorded successfully!';
        if (typeof showToast === 'function') {
          showToast(msg, 'success');
        }
        if (typeof Dashboard !== 'undefined' && Dashboard.refreshData) {
          Dashboard.refreshData();
        }
      }
    } catch (error) {
      this.removeTypingIndicator(typingId);
      this.appendMessage(
        'assistant',
        `⚠️ Sorry, I could not process your request: ${error.message || 'Server error'}. Please check if the backend is running properly.`
      );
    } finally {
      this.isWaitingResponse = false;
      this.sendButton.disabled = false;
      this.inputElement.focus();
    }
  },

  /**
   * Append a message bubble to the chat feed
   */
  appendMessage(role, text) {
    if (!this.messagesContainer) return;

    const messageEl = document.createElement('div');
    messageEl.className = `chat-message ${role}`;

    const avatarEl = document.createElement('div');
    avatarEl.className = 'message-avatar';
    avatarEl.textContent = role === 'user' ? '👤' : '🤖';

    const contentContainer = document.createElement('div');
    contentContainer.style.display = 'flex';
    contentContainer.style.flexDirection = 'column';

    const textEl = document.createElement('div');
    textEl.className = 'message-content';
    textEl.innerHTML = this.formatMarkdown(text);

    const timeEl = document.createElement('div');
    timeEl.className = 'message-time';
    const now = new Date();
    timeEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    contentContainer.appendChild(textEl);
    contentContainer.appendChild(timeEl);

    messageEl.appendChild(avatarEl);
    messageEl.appendChild(contentContainer);

    this.messagesContainer.appendChild(messageEl);
    this.scrollToBottom();
  },

  /**
   * Show animated typing indicator
   */
  showTypingIndicator() {
    const id = 'typing-' + Date.now();
    const indicatorEl = document.createElement('div');
    indicatorEl.id = id;
    indicatorEl.className = 'chat-message assistant';

    const avatarEl = document.createElement('div');
    avatarEl.className = 'message-avatar';
    avatarEl.textContent = '🤖';

    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    contentEl.innerHTML = `
      <div class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    `;

    indicatorEl.appendChild(avatarEl);
    indicatorEl.appendChild(contentEl);

    this.messagesContainer.appendChild(indicatorEl);
    this.scrollToBottom();
    return id;
  },

  /**
   * Remove typing indicator
   */
  removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  },

  /**
   * Simple markdown parser for message formatting
   */
  formatMarkdown(text) {
    if (!text) return '';

    // Sanitize HTML
    let safe = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Code blocks ```code```
    safe = safe.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Inline code `code`
    safe = safe.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold **text**
    safe = safe.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Italic *text*
    safe = safe.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Bullet points
    safe = safe.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
    safe = safe.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Numbered lists
    safe = safe.replace(/^\s*(\d+)\.\s+(.+)$/gm, '<li>$2</li>');

    // Line breaks to <br> (when not inside lists)
    safe = safe.replace(/\n\n/g, '<br><br>');
    safe = safe.replace(/\n/g, '<br>');

    return safe;
  },

  scrollToBottom() {
    if (this.messagesContainer) {
      this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
  }
};

/**
 * Global handler for suggested prompts buttons in the chat UI
 */
function sendSuggestedPrompt(button) {
  if (!button) return;
  // Strip leading emoji
  let text = button.innerText.replace(/^[\p{Emoji}\s]+/u, '').trim();
  Chat.sendMessage(text);
}

// Initialise Chat module once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  Chat.init();
});
