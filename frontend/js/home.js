// Home page logic
function initHomePage() {
    document.getElementById('home-section').style.display = 'flex';
    document.getElementById('analysis-section').style.display = 'none';
    document.getElementById('conference-section').style.display = 'none';

    document.getElementById('search-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const inputId = document.getElementById('paper-id-input').value.trim();
        if (inputId) {
            window.location.href = '?id=' + encodeURIComponent(inputId);
        }
    });

    // Add conference cards after search card
    const homeSection = document.getElementById('home-section');
    if (!document.getElementById('conference-cards-section')) {
        const conferenceSection = document.createElement('div');
        conferenceSection.id = 'conference-cards-section';
        conferenceSection.className = 'recent-section';
        conferenceSection.innerHTML = `
            <h3 class="recent-title">浏览会议论文</h3>
            <div class="conference-cards">
                <a href="?conference=neurips_2025" class="conference-entry-card">
                    <h2>NeurIPS 2025</h2>
                    <p>Neural Information Processing Systems</p>
                </a>
                <a href="?conference=iclr_2026" class="conference-entry-card">
                    <h2>ICLR 2026</h2>
                    <p>International Conference on Learning Representations</p>
                </a>
            </div>
        `;
        homeSection.appendChild(conferenceSection);
    }
}
