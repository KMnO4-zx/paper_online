// Online user statistics
function getOrCreateUserId() {
    let uid = localStorage.getItem('online_user_id');
    if (!uid) {
        uid = crypto.randomUUID();
        localStorage.setItem('online_user_id', uid);
    }
    return uid;
}

const onlineUserId = getOrCreateUserId();

async function updateOnlineCount() {
    try {
        const data = await fetchOnlineCount();
        document.getElementById('online-number').textContent = data.count;
    } catch (e) {}
}

async function sendOnlineHeartbeat() {
    try {
        await sendHeartbeat(onlineUserId);
    } catch (e) {}
}

function initOnlineTracking() {
    sendOnlineHeartbeat();
    updateOnlineCount();
    setInterval(sendOnlineHeartbeat, 20000);
    setInterval(updateOnlineCount, 20000);
}
