// Main initialization
function init() {
    const params = new URLSearchParams(window.location.search);
    const paperId = params.get('id');
    const conference = params.get('conference');
    const search = params.get('search');

    if (conference) {
        initConferencePage(conference);
    } else if (search) {
        initSearchPage(search);
    } else if (paperId) {
        initPaperPage(paperId);
        initChatListeners();
    } else {
        initHomePage();
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
