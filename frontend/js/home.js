function initHomePage() {
    document.getElementById('home-section').style.display = 'block';
    document.getElementById('analysis-section').style.display = 'none';
    document.getElementById('conference-section').style.display = 'none';
    document.getElementById('search-section').style.display = 'none';

    const checkboxes = ['home-search-title', 'home-search-abstract', 'home-search-keywords'];
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

    document.getElementById('search-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const keyword = document.getElementById('search-input').value.trim();
        if (keyword) {
            const params = new URLSearchParams();
            params.append('search', keyword);
            params.append('title', document.getElementById('home-search-title').checked);
            params.append('abstract', document.getElementById('home-search-abstract').checked);
            params.append('keywords', document.getElementById('home-search-keywords').checked);
            window.location.href = '?' + params.toString();
        }
    });
}
