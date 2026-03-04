// API calls
async function fetchPaperInfo(paperId) {
    const res = await fetch(`/paper/${paperId}/info`);
    if (!res.ok) throw new Error('论文未找到');
    return res.json();
}

async function fetchRecentPapers() {
    const res = await fetch('/papers/recent');
    return res.json();
}

async function sendChatMessage(paperId, message, sessionId, userId) {
    return fetch(`/paper/${paperId}/chat`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message, session_id: sessionId, user_id: userId })
    });
}

async function regenerateChatMessage(paperId, message, sessionId, userId) {
    return fetch(`/paper/${paperId}/chat/regenerate`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message, session_id: sessionId, user_id: userId })
    });
}

async function fetchChatSessions(paperId, userId) {
    const res = await fetch(`/paper/${paperId}/chat/sessions?user_id=${userId}`);
    return res.json();
}

async function fetchChatMessages(sessionId) {
    const res = await fetch(`/chat/${sessionId}/messages`);
    return res.json();
}

async function deleteSession(sessionId) {
    await fetch(`/chat/${sessionId}`, { method: 'DELETE' });
}

async function fetchOnlineCount() {
    const res = await fetch('/online/count');
    return res.json();
}

async function sendHeartbeat(userId) {
    await fetch('/online/heartbeat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_id: userId})
    });
}
