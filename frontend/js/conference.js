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

    // Add search button click event
    document.getElementById('conference-search-btn').onclick = () => {
        currentPage = 1;
        loadConferencePapers();
    };

    // Add Shift+Enter key support
    newSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && e.shiftKey) {
            currentPage = 1;
            loadConferencePapers();
        }
    });

    // Ensure at least one checkbox is always checked
    const checkboxes = ['search-title', 'search-abstract', 'search-keywords'];
    checkboxes.forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                const checkedCount = checkboxes.filter(cbId => {
                    const cb = document.getElementById(cbId);
                    return cb && cb.checked;
                }).length;
                if (checkedCount === 0) {
                    e.target.checked = true;
                }
            });
        }
    });

    loadConferencePapers();
}

async function loadConferencePapers() {
    const search = document.getElementById('conference-search').value;
    const params = new URLSearchParams({ page: currentPage, limit: 8 });
    if (search) {
        params.append('search', search);
        params.append('search_title', document.getElementById('search-title').checked);
        params.append('search_abstract', document.getElementById('search-abstract').checked);
        params.append('search_keywords', document.getElementById('search-keywords').checked);
    }

    try {
        // Show loading indicator
        document.getElementById('conference-papers').innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">加载中...</p>';

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
    html += `<input type="number" id="jump-page-input" min="1" max="${pages}" placeholder="页码" style="width: 60px; margin-left: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">`;
    html += `<button onclick="jumpToPage(${pages})">跳转</button>`;
    document.getElementById('conference-pagination').innerHTML = html;
}

function jumpToPage(maxPages) {
    const input = document.getElementById('jump-page-input');
    const pageNum = parseInt(input.value);
    if (pageNum >= 1 && pageNum <= maxPages) {
        goToPage(pageNum);
    }
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
