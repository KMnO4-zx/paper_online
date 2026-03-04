// Home page logic
function initHomePage() {
    document.getElementById('home-section').style.display = 'flex';
    document.getElementById('analysis-section').style.display = 'none';

    document.getElementById('search-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const inputId = document.getElementById('paper-id-input').value.trim();
        if (inputId) {
            window.location.href = '?id=' + encodeURIComponent(inputId);
        }
    });

    fetchRecentPapers().then(papers => {
        if (!papers.length) return;
        const list = document.getElementById('recent-list');
        list.innerHTML = papers.map(p => {
            const kw = (p.keywords || []).slice(0, 3).map(k => `<span class="keyword">${k}</span>`).join('');
            return `<a class="recent-card" href="?id=${p.id}">
                <div class="recent-card-title">${p.title || '无标题'}</div>
                <div class="keywords">${kw}</div>
                <div class="recent-card-abstract">${p.abstract || ''}</div>
            </a>`;
        }).join('');
        document.getElementById('recent-wrapper').style.display = 'block';
    }).catch(() => {});
}
