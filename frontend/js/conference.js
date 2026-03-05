let currentConference = null;
let currentPage = 1;

function initConferencePage(conference) {
    currentConference = conference;
    document.getElementById('home-section').style.display = 'none';
    document.getElementById('analysis-section').style.display = 'none';
    document.getElementById('conference-section').style.display = 'block';

    const titles = {
        'neurips_2025': 'NeurIPS 2025',
        'iclr_2026': 'ICLR 2026'
    };
    const titleElement = document.getElementById('conference-title');
    titleElement.textContent = titles[conference];
    titleElement.style.cursor = 'pointer';
    titleElement.onclick = () => {
        document.getElementById('conference-search').value = '';
        currentPage = 1;
        loadConferencePapers();
    };

    const searchInput = document.getElementById('conference-search');
    searchInput.value = '';

    // Remove old listener and add new one
    const newSearchInput = searchInput.cloneNode(true);
    searchInput.parentNode.replaceChild(newSearchInput, searchInput);

    newSearchInput.addEventListener('input', debounce(() => {
        currentPage = 1;
        loadConferencePapers();
    }, 500));

    loadConferencePapers();
}

async function loadConferencePapers() {
    const search = document.getElementById('conference-search').value;
    const params = new URLSearchParams({ page: currentPage, limit: 8 });
    if (search) params.append('search', search);

    try {
        const res = await fetch(`/conference/${currentConference}/papers?${params}`);
        const data = await res.json();

        renderPapers(data.papers);
        renderPagination(data.page, data.pages);
    } catch (error) {
        console.error('Failed to load papers:', error);
        document.getElementById('conference-papers').innerHTML = '<p style="color: var(--text-secondary); text-align: center;">加载失败，请刷新重试</p>';
    }
}

function renderPapers(papers) {
    const container = document.getElementById('conference-papers');
    if (!papers || papers.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; grid-column: 1/-1;">暂无论文数据</p>';
        return;
    }
    container.innerHTML = papers.map(p => {
        // Process keywords - split by semicolon if needed
        let keywords = [];
        if (p.keywords && Array.isArray(p.keywords)) {
            p.keywords.forEach(k => {
                if (k.includes(';')) {
                    keywords.push(...k.split(';').map(s => s.trim()).filter(s => s));
                } else {
                    keywords.push(k);
                }
            });
        }

        return `
        <a href="?id=${p.id}" class="recent-card">
            <div class="recent-card-title">${p.title}</div>
            <div class="paper-meta">
                ${p.venue ? `<span class="meta-tag venue">${p.venue}</span>` : ''}
                ${p.primary_area ? `<span class="meta-tag primary-area">${p.primary_area}</span>` : ''}
            </div>
            <div class="keywords">
                ${keywords.map(k => `<span class="keyword">${k}</span>`).join('')}
            </div>
            <div class="recent-card-abstract">${p.abstract || ''}</div>
        </a>
    `;
    }).join('');
}

function renderPagination(page, pages) {
    let html = '';
    if (page > 1) html += `<button onclick="goToPage(${page-1})">上一页</button>`;
    html += `<span>第 ${page} / ${pages} 页</span>`;
    if (page < pages) html += `<button onclick="goToPage(${page+1})">下一页</button>`;
    document.getElementById('conference-pagination').innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    loadConferencePapers();
}

function debounce(fn, delay) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}
