// Markdown rendering with math support
function renderMarkdown(text, element) {
    if (typeof marked === 'undefined' || typeof renderMathInElement === 'undefined') {
        console.error('Libraries not loaded');
        element.textContent = text;
        return;
    }

    element.innerHTML = marked.parse(text);

    renderMathInElement(element, {
        delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false}
        ],
        throwOnError: false,
        strict: false
    });
}

// SSE stream handler
async function handleSSEStream(url, onData, onError) {
    const reader = (await fetch(url)).body.getReader();
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
        onData(fullText);
    }
    if (buffer.trim()) {
        for (const line of buffer.split('\n')) {
            if (line.startsWith('data: ')) fullText += line.slice(6);
            else if (line.startsWith('data:')) fullText += line.slice(5);
        }
    }
    return fullText;
}

// Paper marking functions
function getPaperMarks(paperId) {
    const marks = JSON.parse(localStorage.getItem('paperMarks') || '{}');
    return marks[paperId] || { viewed: false, liked: false };
}

function setPaperMark(paperId, markType, value) {
    const marks = JSON.parse(localStorage.getItem('paperMarks') || '{}');
    if (!marks[paperId]) marks[paperId] = { viewed: false, liked: false };
    marks[paperId][markType] = value;
    localStorage.setItem('paperMarks', JSON.stringify(marks));
}

function getStatusIcons(paperId) {
    const marks = getPaperMarks(paperId);
    let icons = '';
    if (marks.viewed) icons += '<span class="status-icon">👁️</span>';
    if (marks.liked) icons += '<span class="status-icon">❤️</span>';
    return icons;
}
