let searchCurrentPage = 1;
let searchKeyword = '';

function initSearchPage(keyword) {
    searchKeyword = keyword;
    document.getElementById('home-section').style.display = 'none';
    document.getElementById('analysis-section').style.display = 'none';
    document.getElementById('conference-section').style.display = 'none';
    document.getElementById('search-section').style.display = 'block';

    const params = new URLSearchParams(window.location.search);
    const searchInput = document.getElementById('global-search-input');
    searchInput.value = keyword;

    // Set checkbox states from URL params
    document.getElementById('global-search-title').checked = params.get('title') !== 'false';
    document.getElementById('global-search-abstract').checked = params.get('abstract') !== 'false';
    document.getElementById('global-search-keywords').checked = params.get('keywords') !== 'false';

    const newSearchInput = searchInput.cloneNode(true);
    searchInput.parentNode.replaceChild(newSearchInput, searchInput);

    document.getElementById('global-search-btn').onclick = () => {
        const newKeyword = document.getElementById('global-search-input').value.trim();
        if (newKeyword) {
            const urlParams = new URLSearchParams();
            urlParams.append('search', newKeyword);
            urlParams.append('title', document.getElementById('global-search-title').checked);
            urlParams.append('abstract', document.getElementById('global-search-abstract').checked);
            urlParams.append('keywords', document.getElementById('global-search-keywords').checked);
            window.location.href = '?' + urlParams.toString();
        }
    };

    document.getElementById('global-search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && e.shiftKey) {
            const newKeyword = document.getElementById('global-search-input').value.trim();
            if (newKeyword) {
                const urlParams = new URLSearchParams();
                urlParams.append('search', newKeyword);
                urlParams.append('title', document.getElementById('global-search-title').checked);
                urlParams.append('abstract', document.getElementById('global-search-abstract').checked);
                urlParams.append('keywords', document.getElementById('global-search-keywords').checked);
                window.location.href = '?' + urlParams.toString();
            }
        }
    });

    const checkboxes = ['global-search-title', 'global-search-abstract', 'global-search-keywords'];
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

    loadSearchResults();
}

async function loadSearchResults() {
    const params = new URLSearchParams({ page: searchCurrentPage, limit: 8 });
    if (searchKeyword) {
        params.append('search', searchKeyword);
        params.append('search_title', document.getElementById('global-search-title').checked);
        params.append('search_abstract', document.getElementById('global-search-abstract').checked);
        params.append('search_keywords', document.getElementById('global-search-keywords').checked);
    }

    try {
        document.getElementById('search-papers').innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">加载中...</p>';

        const res = await fetch(`/search/papers?${params}`);
        const data = await res.json();

        renderSearchPapers(data.papers);
        renderSearchPagination(data.page, data.pages);
    } catch (error) {
        console.error('Failed to load papers:', error);
        document.getElementById('search-papers').innerHTML = '<p style="color: var(--text-secondary); text-align: center;">加载失败，请刷新重试</p>';
    }
}

function renderSearchPapers(papers) {
    const container = document.getElementById('search-papers');
    if (!papers || papers.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; grid-column: 1/-1;">暂无论文数据</p>';
        return;
    }
    container.innerHTML = papers.map((p, index) => {
        const paperNumber = (searchCurrentPage - 1) * 8 + index + 1;

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
            <div class="recent-card-title">
                <span class="paper-number">${paperNumber}</span>
                ${p.title}
            </div>
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

function renderSearchPagination(page, pages) {
    let html = '';
    if (page > 1) html += `<button onclick="goToSearchPage(${page-1})">上一页</button>`;
    html += `<span>第 ${page} / ${pages} 页</span>`;
    if (page < pages) html += `<button onclick="goToSearchPage(${page+1})">下一页</button>`;
    html += `<input type="number" id="search-jump-page-input" min="1" max="${pages}" placeholder="页码" style="width: 60px; margin-left: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">`;
    html += `<button onclick="jumpToSearchPage(${pages})">跳转</button>`;
    document.getElementById('search-pagination').innerHTML = html;
}

function goToSearchPage(page) {
    searchCurrentPage = page;
    loadSearchResults();
}

function jumpToSearchPage(maxPages) {
    const input = document.getElementById('search-jump-page-input');
    const pageNum = parseInt(input.value);
    if (pageNum >= 1 && pageNum <= maxPages) {
        goToSearchPage(pageNum);
    }
}
