// Main initialization
function init() {
    const urlPaperId = new URLSearchParams(window.location.search).get('id');

    if (!urlPaperId) {
        initHomePage();
    } else {
        initPaperPage(urlPaperId);
        initChatListeners();
    }

    initOnlineTracking();
}

function waitForLibraries(callback, maxAttempts = 50) {
    let attempts = 0;
    const check = setInterval(() => {
        attempts++;
        if (typeof marked !== 'undefined' && typeof renderMathInElement !== 'undefined') {
            clearInterval(check);
            callback();
        } else if (attempts >= maxAttempts) {
            clearInterval(check);
            console.error('Failed to load required libraries');
            callback();
        }
    }, 100);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => waitForLibraries(init));
} else {
    waitForLibraries(init);
}
