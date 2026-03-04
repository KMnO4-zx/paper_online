// Chat functionality
function getUserId() {
    let uid = localStorage.getItem('paper_user_id');
    if (!uid) {
        uid = crypto.randomUUID();
        localStorage.setItem('paper_user_id', uid);
    }
    return uid;
}

const userId = getUserId();
let currentSessionId = null;
let chatSending = false;
let lastUserMsg = null;

function newChatSession() {
    currentSessionId = crypto.randomUUID();
    const msgEl = document.getElementById('chat-messages');
    msgEl.innerHTML = '<div class="chat-empty">输入问题，开始与论文对话</div>';
    document.querySelectorAll('.session-tab').forEach(t => t.classList.remove('active'));
}

function toggleSidebar() {
    document.querySelector('.chat-sidebar').classList.toggle('hidden');
}

function appendChatMsg(role, content) {
    const msgEl = document.getElementById('chat-messages');
    const empty = msgEl.querySelector('.chat-empty');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = `chat-msg ${role}`;
    if (role === 'assistant') {
        renderMarkdown(content, div);
    } else {
        div.textContent = content;
    }
    msgEl.appendChild(div);
    msgEl.scrollTop = msgEl.scrollHeight;
    return div;
}

async function sendChat() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg || chatSending || !paperId) return;

    if (!currentSessionId) currentSessionId = crypto.randomUUID();

    chatSending = true;
    document.getElementById('chat-send-btn').disabled = true;
    input.value = '';

    appendChatMsg('user', msg);
    const assistantDiv = appendChatMsg('assistant', '');
    assistantDiv.textContent = '...';

    try {
        const res = await sendChatMessage(paperId, msg, currentSessionId, userId);
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
            const parts = buffer.split('\n\n');
            buffer = parts.pop();
            for (const event of parts) {
                const dataLines = [];
                for (const line of event.split('\n')) {
                    if (line.startsWith('data: ')) dataLines.push(line.slice(6));
                    else if (line.startsWith('data:')) dataLines.push(line.slice(5));
                }
                if (dataLines.length) fullText += dataLines.join('\n');
            }
            assistantDiv.textContent = fullText;
        }
        if (buffer.trim()) {
            for (const line of buffer.split('\n')) {
                if (line.startsWith('data: ')) fullText += line.slice(6);
                else if (line.startsWith('data:')) fullText += line.slice(5);
            }
        }
        renderMarkdown(fullText, assistantDiv);
        lastUserMsg = msg;
        showRegenerateBtn();
        loadSessions();
    } catch (e) {
        assistantDiv.textContent = '发送失败: ' + e.message;
    }

    chatSending = false;
    document.getElementById('chat-send-btn').disabled = false;
}

function showRegenerateBtn() {
    document.querySelectorAll('.chat-regenerate-btn').forEach(b => b.remove());
    const btn = document.createElement('button');
    btn.className = 'chat-regenerate-btn';
    btn.textContent = '重新回复';
    btn.onclick = regenerateChat;
    document.getElementById('chat-messages').appendChild(btn);
}

async function regenerateChat() {
    if (!lastUserMsg || chatSending || !currentSessionId) return;
    chatSending = true;
    document.getElementById('chat-send-btn').disabled = true;
    document.querySelectorAll('.chat-regenerate-btn').forEach(b => b.remove());

    const msgs = document.getElementById('chat-messages');
    const lastAssistant = msgs.querySelector('.chat-msg.assistant:last-of-type');
    if (lastAssistant) lastAssistant.remove();

    const assistantDiv = appendChatMsg('assistant', '');
    assistantDiv.textContent = '...';

    try {
        const res = await regenerateChatMessage(paperId, lastUserMsg, currentSessionId, userId);
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
            const parts = buffer.split('\n\n');
            buffer = parts.pop();
            for (const event of parts) {
                const dataLines = [];
                for (const line of event.split('\n')) {
                    if (line.startsWith('data: ')) dataLines.push(line.slice(6));
                    else if (line.startsWith('data:')) dataLines.push(line.slice(5));
                }
                if (dataLines.length) fullText += dataLines.join('\n');
            }
            assistantDiv.textContent = fullText;
        }
        if (buffer.trim()) {
            for (const line of buffer.split('\n')) {
                if (line.startsWith('data: ')) fullText += line.slice(6);
                else if (line.startsWith('data:')) fullText += line.slice(5);
            }
        }
        renderMarkdown(fullText, assistantDiv);
        showRegenerateBtn();
    } catch (e) {
        assistantDiv.textContent = '重新回复失败: ' + e.message;
    }

    chatSending = false;
    document.getElementById('chat-send-btn').disabled = false;
}

async function loadSessions() {
    if (!paperId) return;
    try {
        const sessions = await fetchChatSessions(paperId, userId);
        const container = document.getElementById('chat-sessions');
        container.innerHTML = sessions.map(s =>
            `<div class="session-tab ${s.id === currentSessionId ? 'active' : ''}" onclick="switchSession('${s.id}')"><span class="title">${s.title}</span><button class="del-btn" onclick="event.stopPropagation();deleteSessionById('${s.id}')">&times;</button></div>`
        ).join('');
    } catch {}
}

async function deleteSessionById(sessionId) {
    try {
        await deleteSession(sessionId);
    } catch {}
    if (currentSessionId === sessionId) {
        currentSessionId = null;
        document.getElementById('chat-messages').innerHTML = '<div class="chat-empty">输入问题，开始与论文对话</div>';
    }
    loadSessions();
}

async function switchSession(sessionId) {
    currentSessionId = sessionId;
    const msgEl = document.getElementById('chat-messages');
    msgEl.innerHTML = '<div class="loading"><div class="spinner"></div><span>加载中...</span></div>';

    document.querySelectorAll('.session-tab').forEach(t => {
        t.classList.toggle('active', t.getAttribute('onclick').includes(sessionId));
    });

    try {
        const messages = await fetchChatMessages(sessionId);
        msgEl.innerHTML = '';
        if (!messages.length) {
            msgEl.innerHTML = '<div class="chat-empty">输入问题，开始与论文对话</div>';
            return;
        }
        messages.forEach(m => appendChatMsg(m.role, m.content));
        const lastUser = [...messages].reverse().find(m => m.role === 'user');
        if (lastUser) {
            lastUserMsg = lastUser.content;
            showRegenerateBtn();
        }
    } catch {
        msgEl.innerHTML = '<div class="error">加载失败</div>';
    }
}

function initChatListeners() {
    document.getElementById('chat-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.shiftKey) {
            e.preventDefault();
            sendChat();
        }
    });

    document.getElementById('chat-input').addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });

    if (paperId) loadSessions();
}
