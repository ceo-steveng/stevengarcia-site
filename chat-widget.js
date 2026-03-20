/**
 * Steven Garcia AI Chat Widget
 * Client-side chatbot using Gemini Flash — knows only public website content.
 * No server, no sensitive data, no access to backend systems.
 */
(function() {
  'use strict';

  const GEMINI_KEY = 'AIzaSyBQrDb-zf66h5ix34EQU6v-itYdawj8eG8';
  const GEMINI_MODEL = 'gemini-2.0-flash';
  const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${GEMINI_KEY}`;

  const SYSTEM_PROMPT = `You are an AI assistant on Steven Garcia's website (stevengarcia.me). Your job is to answer questions about Steven, his work, and his consulting services.

WHO STEVEN IS:
- New Car Manager at Ancira Kia in San Antonio, TX
- Runs a 200+ unit/month new car operation
- Built AI automation systems for his own dealership (morning reports, CRM task automation, email triage, desk logs, inventory tracking, save-a-deal meetings)
- Now consults with other dealerships to build similar systems

CONSULTING SERVICES (stevengarcia.me/ai-setup/):
- Starter Package ($1,000): 2-hour strategy session + custom automation roadmap + 30-day email support
- Full Desk Package ($3,500): Everything in Starter + 3 custom automations built + staff training session + 60-day support
- Full Stack Package ($7,500): Everything in Full Desk + complete AI infrastructure + CRM integration + 90-day support + monthly optimization calls
- Book a call: calendly.com/stevengarcia/30min

THE DEALERSHIP PLAYBOOK ($197):
- 37-page PDF, 12 chapters covering dealership operations and AI adoption
- Available at stevengarcia.me/playbook/
- Includes coaching upsell ($500 for 1-on-1 coaching call)

BLOG POSTS (stevengarcia.me/blog/):
- "How I Use AI to Run a 200-Unit Kia Store"
- "The Dealership Morning Report: 21 Metrics That Replace Your Spreadsheet"
- "How I Automated My Morning Report as a Dealership Manager"
- "I Had 847 CRM Tasks. AI Cleared 790 of Them."
- "The Save-a-Deal Meeting: A 10-Minute Format That Catches Every Missed Deal"
- "The Exact VinSolutions Automation Stack I Run in Production"

SOCIAL MEDIA:
- X/Twitter: @ceo_steveng
- LinkedIn: linkedin.com/in/stevengarcia4/
- Instagram: @ceo.steveng
- YouTube: @ceosteveng
- TikTok: @ceo_steveng

RULES:
- Be helpful, direct, and concise. No fluff.
- If someone asks about consulting, point them to the packages page or Calendly link.
- If someone asks about specific automation capabilities, reference the blog posts.
- If someone asks about pricing, give the real numbers above.
- You do NOT have access to Steven's personal information, dealership internal data, customer data, inventory, or any backend systems.
- If asked about things you don't know, say "I don't have that info — reach out to Steven directly" and link to Calendly.
- Keep responses under 150 words unless the question requires detail.
- Don't pretend to be Steven. You're his website assistant.
- No markdown formatting — plain text only (the chat widget doesn't render markdown).`;

  let chatHistory = [];
  let isOpen = false;
  let isTyping = false;

  // Inject styles
  const style = document.createElement('style');
  style.textContent = `
    #sg-chat-btn {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: #C0392B;
      border: none;
      cursor: pointer;
      z-index: 9999;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 16px rgba(192,57,43,0.4);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    #sg-chat-btn:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 24px rgba(192,57,43,0.5);
    }
    #sg-chat-btn svg {
      width: 26px;
      height: 26px;
      fill: #FFFFFF;
    }

    #sg-chat-window {
      position: fixed;
      bottom: 92px;
      right: 24px;
      width: 380px;
      max-width: calc(100vw - 32px);
      height: 520px;
      max-height: calc(100vh - 120px);
      background: #0A0A0A;
      border: 1px solid #1F1F1F;
      border-radius: 16px;
      z-index: 99999;
      display: none;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 12px 48px rgba(0,0,0,0.6);
      font-family: 'DM Sans', -apple-system, sans-serif;
    }
    #sg-chat-window.open {
      display: flex;
    }

    #sg-chat-header {
      padding: 16px 20px;
      border-bottom: 1px solid #1F1F1F;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
    }
    #sg-chat-header h3 {
      color: #FFFFFF;
      font-family: 'Barlow Condensed', sans-serif;
      font-weight: 600;
      font-size: 16px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin: 0;
    }
    #sg-chat-header span {
      color: #666;
      font-size: 11px;
      font-weight: 400;
    }
    #sg-chat-close {
      background: none;
      border: none;
      color: #666;
      font-size: 20px;
      cursor: pointer;
      padding: 4px 8px;
      line-height: 1;
      transition: color 0.15s;
    }
    #sg-chat-close:hover { color: #FFFFFF; }

    #sg-chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    #sg-chat-messages::-webkit-scrollbar { width: 4px; }
    #sg-chat-messages::-webkit-scrollbar-track { background: transparent; }
    #sg-chat-messages::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }

    .sg-msg {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.5;
      color: #FFFFFF;
      word-wrap: break-word;
    }
    .sg-msg.bot {
      align-self: flex-start;
      background: #1A1A1A;
      border: 1px solid #2A2A2A;
      border-top-left-radius: 4px;
    }
    .sg-msg.user {
      align-self: flex-end;
      background: #C0392B;
      border-top-right-radius: 4px;
    }
    .sg-msg.typing {
      align-self: flex-start;
      background: #1A1A1A;
      border: 1px solid #2A2A2A;
      border-top-left-radius: 4px;
      color: #666;
      font-style: italic;
    }

    .sg-msg a {
      color: #E74C3C;
      text-decoration: underline;
    }

    #sg-chat-input-area {
      padding: 12px 16px;
      border-top: 1px solid #1F1F1F;
      display: flex;
      gap: 8px;
      flex-shrink: 0;
    }
    #sg-chat-input {
      flex: 1;
      background: #111;
      border: 1px solid #2A2A2A;
      border-radius: 8px;
      padding: 10px 14px;
      color: #FFFFFF;
      font-family: 'DM Sans', sans-serif;
      font-size: 14px;
      outline: none;
      transition: border-color 0.15s;
    }
    #sg-chat-input::placeholder { color: #555; }
    #sg-chat-input:focus { border-color: #C0392B; }

    #sg-chat-send {
      background: #C0392B;
      border: none;
      border-radius: 8px;
      padding: 10px 16px;
      color: #FFFFFF;
      cursor: pointer;
      font-family: 'DM Sans', sans-serif;
      font-size: 14px;
      font-weight: 500;
      transition: background 0.15s;
      flex-shrink: 0;
    }
    #sg-chat-send:hover { background: #E74C3C; }
    #sg-chat-send:disabled { background: #333; cursor: not-allowed; }

    .sg-chat-hidden { display: none !important; }

    @media (max-width: 600px) {
      #sg-chat-window.open {
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100% !important;
        height: 100% !important;
        max-width: 100% !important;
        max-height: 100% !important;
        border-radius: 0 !important;
        border: none !important;
        z-index: 999999 !important;
      }
      #sg-chat-window.open #sg-chat-header {
        padding-top: 50px;
      }
      #sg-chat-window.open #sg-chat-input-area {
        padding-bottom: 20px;
      }
      #sg-chat-window.open #sg-chat-close {
        font-size: 32px;
        padding: 8px 16px;
        min-width: 48px;
        min-height: 48px;
        color: #FFFFFF;
      }
      #sg-chat-btn { bottom: 20px; right: 20px; width: 50px; height: 50px; }
      #sg-chat-btn svg { width: 22px; height: 22px; }
    }
  `;
  document.head.appendChild(style);

  // Chat button
  const btn = document.createElement('button');
  btn.id = 'sg-chat-btn';
  btn.setAttribute('aria-label', 'Open chat');
  btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.2L4 17.2V4h16v12z"/></svg>';
  btn.onclick = toggleChat;
  document.body.appendChild(btn);

  // Chat window
  const win = document.createElement('div');
  win.id = 'sg-chat-window';
  win.innerHTML = `
    <div id="sg-chat-header">
      <div>
        <h3>Ask me anything</h3>
        <span>AI assistant — stevengarcia.me</span>
      </div>
      <button id="sg-chat-close" aria-label="Close chat">&times;</button>
    </div>
    <div id="sg-chat-messages"></div>
    <div id="sg-chat-input-area">
      <input id="sg-chat-input" type="text" placeholder="Type a question..." autocomplete="off" />
      <button id="sg-chat-send">Send</button>
    </div>
  `;
  document.body.appendChild(win);

  document.getElementById('sg-chat-close').onclick = toggleChat;
  document.getElementById('sg-chat-send').onclick = sendMessage;
  document.getElementById('sg-chat-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Welcome message
  addBotMessage("Hey! I'm Steven's AI assistant. Ask me about his consulting services, the dealership playbook, blog posts, or how he uses AI to run a 200-unit store. What can I help with?");

  function toggleChat() {
    isOpen = !isOpen;
    win.classList.toggle('open', isOpen);
    var mobile = window.innerWidth <= 600;
    if (mobile) {
      btn.classList.toggle('sg-chat-hidden', isOpen);
      if (isOpen) {
        // Set height explicitly to window.innerHeight for iOS Safari
        win.style.height = window.innerHeight + 'px';
        document.body.style.overflow = 'hidden';
      } else {
        win.style.height = '';
        document.body.style.overflow = '';
      }
    }
    if (isOpen) {
      setTimeout(function() {
        document.getElementById('sg-chat-input').focus();
      }, 300);
    }
  }

  function addBotMessage(text) {
    const messages = document.getElementById('sg-chat-messages');
    const div = document.createElement('div');
    div.className = 'sg-msg bot';
    div.textContent = text;
    // Auto-link URLs
    div.innerHTML = div.textContent.replace(
      /(https?:\/\/[^\s<]+|calendly\.com\/[^\s<]+|stevengarcia\.me[^\s<]*)/g,
      '<a href="$1" target="_blank" rel="noopener">$1</a>'
    ).replace(
      /href="(?!https?:\/\/)/g,
      'href="https://'
    );
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function addUserMessage(text) {
    const messages = document.getElementById('sg-chat-messages');
    const div = document.createElement('div');
    div.className = 'sg-msg user';
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    const messages = document.getElementById('sg-chat-messages');
    const div = document.createElement('div');
    div.className = 'sg-msg typing';
    div.id = 'sg-typing';
    div.textContent = 'Thinking...';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function removeTyping() {
    const el = document.getElementById('sg-typing');
    if (el) el.remove();
  }

  async function sendMessage() {
    const input = document.getElementById('sg-chat-input');
    const text = input.value.trim();
    if (!text || isTyping) return;

    input.value = '';
    addUserMessage(text);

    chatHistory.push({ role: 'user', parts: [{ text }] });

    isTyping = true;
    document.getElementById('sg-chat-send').disabled = true;
    showTyping();

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system_instruction: { parts: [{ text: SYSTEM_PROMPT }] },
          contents: chatHistory,
          generationConfig: {
            temperature: 0.7,
            maxOutputTokens: 512,
            topP: 0.9
          },
          safetySettings: [
            { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
            { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
            { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
            { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' }
          ]
        })
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();
      const reply = data.candidates?.[0]?.content?.parts?.[0]?.text || "Sorry, I couldn't process that. Try again or reach out to Steven directly at calendly.com/stevengarcia/30min";

      chatHistory.push({ role: 'model', parts: [{ text: reply }] });

      // Keep history manageable (last 20 messages)
      if (chatHistory.length > 20) {
        chatHistory = chatHistory.slice(-20);
      }

      removeTyping();
      addBotMessage(reply);
    } catch (err) {
      removeTyping();
      addBotMessage("Something went wrong. Try again, or reach out to Steven directly at calendly.com/stevengarcia/30min");
      console.error('Chat error:', err);
    } finally {
      isTyping = false;
      document.getElementById('sg-chat-send').disabled = false;
      document.getElementById('sg-chat-input').focus();
    }
  }
})();
