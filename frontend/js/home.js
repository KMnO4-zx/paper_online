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
}
