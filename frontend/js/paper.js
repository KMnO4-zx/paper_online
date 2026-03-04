// Paper details page logic
let paperId = null;

function initPaperPage(id) {
    paperId = id;
    document.getElementById('home-section').style.display = 'none';
    document.getElementById('analysis-section').style.display = 'flex';
    loadPaperInfo();
    loadAnalysis();
}

async function loadPaperInfo() {
    try {
        const data = await fetchPaperInfo(paperId);
        document.getElementById('paper-title').textContent = data.title || '无标题';

        const abstractEl = document.getElementById('abstract');
        renderMarkdown(data.abstract || '无摘要', abstractEl);

        const keywordsEl = document.getElementById('keywords');
        const keywords = data.keywords || [];
        keywordsEl.innerHTML = keywords.map(k => `<span class="keyword">${k}</span>`).join('');

        document.getElementById('openreview-link').href = `https://openreview.net/forum?id=${paperId}`;
        document.getElementById('pdf-link').href = data.pdf || '#';

        document.getElementById('paper-loading').style.display = 'none';
        document.getElementById('paper-content').style.display = 'block';
    } catch (e) {
        document.getElementById('paper-loading').innerHTML = `<div class="error">加载失败: ${e.message}</div>`;
    }
}

function reanalyze() {
    document.getElementById('reanalyze-btn').style.display = 'none';
    document.getElementById('llm-response').innerHTML = '';
    const loadingEl = document.getElementById('llm-loading');
    loadingEl.style.display = 'flex';
    loadingEl.innerHTML = '<div class="spinner"></div><span>正在重新分析论文...</span>';
    loadAnalysis(true);
}

function loadAnalysis(reanalyze = false) {
    const responseEl = document.getElementById('llm-response');
    const loadingEl = document.getElementById('llm-loading');
    const statusText = loadingEl.querySelector('span');
    let fullText = '';

    const url = reanalyze ? `/paper/${paperId}?reanalyze=true` : `/paper/${paperId}`;
    const eventSource = new EventSource(url);

    eventSource.addEventListener('status', (event) => {
        statusText.textContent = event.data;
    });

    eventSource.addEventListener('error', (event) => {
        eventSource.close();
        loadingEl.innerHTML = `<div class="error">${event.data}</div>`;
    });

    eventSource.addEventListener('done', () => {
        eventSource.close();
        if (fullText) {
            renderMarkdown(fullText, responseEl);
            document.getElementById('reanalyze-btn').style.display = 'inline-flex';
        }
    });

    eventSource.onmessage = (event) => {
        loadingEl.style.display = 'none';
        fullText += event.data;
        responseEl.textContent = fullText;
    };

    eventSource.onerror = () => {
        eventSource.close();
        if (fullText && !responseEl.innerHTML) {
            renderMarkdown(fullText, responseEl);
            document.getElementById('reanalyze-btn').style.display = 'inline-flex';
        } else if (!fullText && !loadingEl.querySelector('.error')) {
            loadingEl.innerHTML = '<div class="error">连接失败，请稍后重试</div>';
        }
    };
}
