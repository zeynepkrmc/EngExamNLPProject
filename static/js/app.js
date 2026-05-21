/**
 * app.js — YÖKDİL NLP Frontend
 * Serbest Metin Analizi, Cloze Test, Sonuçlar
 */

// ── DURUM YÖNETİMİ ──
const state = {
    questions: [],
    currentIndex: 0,
    userCorrect: 0,
    modelCorrect: 0,
    answered: 0,
};

// ── SAYFA YÜKLENDİĞİNDE ──
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    loadStats();
    loadQuestions();

    document.getElementById('btnAnalyze').addEventListener('click', analyzeText);
    document.getElementById('btnNext').addEventListener('click', nextQuestion);
    document.getElementById('btnRunTest').addEventListener('click', runFullTest);
});

// ── SEKME NAVİGASYONU ──
function setupNavigation() {
    document.querySelectorAll('[data-tab]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = e.currentTarget.getAttribute('data-tab');

            // Aktif link güncelle
            document.querySelectorAll('[data-tab]').forEach(l => l.classList.remove('active'));
            e.currentTarget.classList.add('active');

            // Panel göster
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            const panelId = 'panel' + tab.charAt(0).toUpperCase() + tab.slice(1);
            const panel = document.getElementById(panelId);
            if (panel) panel.classList.add('active');
        });
    });
}

// ── MODEL İSTATİSTİKLERİ ──
async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();

        document.getElementById('statCorpus').textContent = formatNumber(data.corpus_size);
        document.getElementById('statBigram').textContent = formatNumber(data.unique_bigrams);
        document.getElementById('statTrigram').textContent = formatNumber(data.unique_trigrams);
        document.getElementById('statQuestions').textContent = data.test_set_size || '0';
    } catch (err) {
        console.error('İstatistik yükleme hatası:', err);
    }
}

// ── SERBEST METİN ANALİZİ ──
async function analyzeText() {
    const text = document.getElementById('inputText').value.trim();
    if (!text) {
        alert('Lütfen analiz edilecek bir metin girin.');
        return;
    }

    const btn = document.getElementById('btnAnalyze');
    btn.innerHTML = '<span class="loading-spinner"></span>Analiz ediliyor...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await res.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        displayAnalysis(data);
    } catch (err) {
        alert('Analiz sırasında hata oluştu: ' + err.message);
    } finally {
        btn.innerHTML = '<i class="bi bi-cpu me-2"></i>Analiz Et';
        btn.disabled = false;
    }
}

function displayAnalysis(data) {
    document.getElementById('analysisPlaceholder').style.display = 'none';
    const results = document.getElementById('analysisResults');
    results.style.display = 'block';

    let html = `
        <div class="analysis-stat"><span class="label">Kelime Sayısı</span><span class="value">${data.word_count}</span></div>
        <div class="analysis-stat"><span class="label">Benzersiz Kelime</span><span class="value">${data.unique_words}</span></div>
        <div class="analysis-stat"><span class="label">Cümle Sayısı</span><span class="value">${data.sentence_count}</span></div>
        <div class="analysis-stat"><span class="label">Bigram Tipi</span><span class="value">${data.total_bigram_types}</span></div>
        <div class="analysis-stat"><span class="label">Trigram Tipi</span><span class="value">${data.total_trigram_types}</span></div>
    `;

    if (data.bigram_matches && data.bigram_matches.length > 0) {
        html += `<div class="ngram-section-title">Bigram Eşleşmeleri (Corpus)</div>`;
        data.bigram_matches.forEach(m => {
            html += `<div class="ngram-match">
                <span class="ngram-text">${m.ngram}</span>
                <span class="ngram-freq">×${m.corpus_freq}</span>
            </div>`;
        });
    }

    if (data.trigram_matches && data.trigram_matches.length > 0) {
        html += `<div class="ngram-section-title">Trigram Eşleşmeleri (Corpus)</div>`;
        data.trigram_matches.forEach(m => {
            html += `<div class="ngram-match">
                <span class="ngram-text">${m.ngram}</span>
                <span class="ngram-freq">×${m.corpus_freq}</span>
            </div>`;
        });
    }

    if (data.quadgram_matches && data.quadgram_matches.length > 0) {
        html += `<div class="ngram-section-title">Quadgram Eşleşmeleri (Corpus)</div>`;
        data.quadgram_matches.forEach(m => {
            html += `<div class="ngram-match">
                <span class="ngram-text">${m.ngram}</span>
                <span class="ngram-freq">×${m.corpus_freq}</span>
            </div>`;
        });
    }

    if ((!data.bigram_matches || data.bigram_matches.length === 0) &&
        (!data.trigram_matches || data.trigram_matches.length === 0)) {
        html += `<div class="ngram-section-title" style="color:var(--warning);">
            Corpus'ta eşleşen n-gram bulunamadı
        </div>`;
    }

    document.getElementById('analysisContent').innerHTML = html;
}

// ── CLOZE TEST ──
async function loadQuestions() {
    try {
        const res = await fetch('/api/questions');
        const data = await res.json();
        state.questions = data.questions || [];

        if (state.questions.length > 0) {
            renderQuestion();
        } else {
            document.getElementById('questionText').textContent =
                'Test seti bulunamadı. Lütfen önce question_extractor.py çalıştırın.';
        }
    } catch (err) {
        document.getElementById('questionText').textContent =
            'Sorular yüklenirken hata oluştu. Backend çalışıyor mu?';
        console.error(err);
    }
}

function renderQuestion() {
    const q = state.questions[state.currentIndex];
    if (!q) return;

    // Soru numarası güncelle
    document.getElementById('scoreQuestion').textContent =
        `${state.currentIndex + 1} / ${state.questions.length}`;

    // Kaynak
    document.getElementById('questionSource').textContent =
        `Kaynak: ${q.source || '—'} | Soru #${q.id}`;

    // Soru metni — boşluğu vurgula
    const text = (q.question_text || '').replace(
        /-{3,}/g,
        '<span class="blank">________</span>'
    );
    document.getElementById('questionText').innerHTML = text;

    // Şıkları render et
    const grid = document.getElementById('optionsGrid');
    grid.innerHTML = '';

    const letters = ['A', 'B', 'C', 'D', 'E'];
    letters.forEach(letter => {
        if (!q.options[letter]) return;
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.innerHTML = `
            <span class="option-letter">${letter}</span>
            <span class="option-text">${q.options[letter]}</span>
        `;
        btn.addEventListener('click', () => selectOption(letter));
        grid.appendChild(btn);
    });

    // Feedback ve next gizle
    document.getElementById('feedbackArea').style.display = 'none';
    document.getElementById('btnNext').style.display = 'none';
}

async function selectOption(userChoice) {
    const q = state.questions[state.currentIndex];

    // Butonları devre dışı bırak
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.add('disabled');
    });

    // Modelden tahmin al
    try {
        const res = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question_id: q.id })
        });
        const data = await res.json();

        const correctAnswer = data.correct_answer;
        const modelAnswer = data.predicted_answer;

        // Kullanıcı doğru mu?
        const userCorrect = (userChoice === correctAnswer);
        // Model doğru mu?
        const modelCorrectQ = (modelAnswer === correctAnswer);

        if (userCorrect) state.userCorrect++;
        if (modelCorrectQ) state.modelCorrect++;
        state.answered++;

        // Skorları güncelle
        document.getElementById('scoreUser').textContent = state.userCorrect;
        document.getElementById('scoreModel').textContent = state.modelCorrect;

        // Butonları renklendir
        document.querySelectorAll('.option-btn').forEach(btn => {
            const letter = btn.querySelector('.option-letter').textContent;

            if (letter === correctAnswer) {
                btn.classList.add('correct');
            }
            if (letter === userChoice && !userCorrect) {
                btn.classList.add('wrong');
            }
            if (letter === modelAnswer) {
                btn.classList.add('model-pick');
            }
        });

        // Feedback göster
        const feedback = document.getElementById('feedbackArea');
        feedback.style.display = 'block';

        if (userCorrect) {
            feedback.className = 'feedback-area correct';
            feedback.innerHTML = `
                <strong>✅ Doğru!</strong> Cevap: ${correctAnswer}) ${q.options[correctAnswer]}<br>
                <small>Model tahmini: ${modelAnswer} ${modelCorrectQ ? '✅' : '❌'} |
                Skorlar: ${Object.entries(data.scores).map(([k, v]) => `${k}:${v}`).join(', ')}</small>
            `;
        } else {
            feedback.className = 'feedback-area wrong';
            feedback.innerHTML = `
                <strong>❌ Yanlış!</strong> Sizin cevap: ${userChoice} | Doğru cevap: ${correctAnswer}) ${q.options[correctAnswer]}<br>
                <small>Model tahmini: ${modelAnswer} ${modelCorrectQ ? '✅' : '❌'} |
                Skorlar: ${Object.entries(data.scores).map(([k, v]) => `${k}:${v}`).join(', ')}</small>
            `;
        }

        // Sonraki soru butonu
        if (state.currentIndex < state.questions.length - 1) {
            document.getElementById('btnNext').style.display = 'inline-block';
        }

    } catch (err) {
        console.error('Tahmin hatası:', err);
        alert('Model tahmini alınırken hata oluştu.');
    }
}

function nextQuestion() {
    state.currentIndex++;
    renderQuestion();
}

// ── SONUÇLAR: TAM TEST ──
let pieChart = null;
let barChart = null;
let ngramChart = null;
let distChart = null;

async function runFullTest() {
    const btn = document.getElementById('btnRunTest');
    btn.innerHTML = '<span class="loading-spinner"></span>Test çalıştırılıyor...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/test');
        const data = await res.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        displayTestResults(data);
    } catch (err) {
        alert('Test çalıştırılırken hata oluştu: ' + err.message);
    } finally {
        btn.innerHTML = '<i class="bi bi-play-circle me-2"></i>Tüm Testi Çalıştır';
        btn.disabled = false;
    }
}

function displayTestResults(data) {
    document.getElementById('testResultsArea').style.display = 'block';

    // Metrikler
    document.getElementById('metricAccuracy').textContent = data.accuracy_pct || `${(data.accuracy * 100).toFixed(1)}%`;
    document.getElementById('metricCorrect').textContent = `${data.correct} / ${data.total}`;
    document.getElementById('metricWrong').textContent = `${data.total - data.correct}`;

    // ── 1. Pie Chart: Doğru/Yanlış ──
    const ctxPie = document.getElementById('chartPie').getContext('2d');
    if (pieChart) pieChart.destroy();
    pieChart = new Chart(ctxPie, {
        type: 'doughnut',
        data: {
            labels: ['Doğru', 'Yanlış'],
            datasets: [{
                data: [data.correct, data.total - data.correct],
                backgroundColor: ['#22c55e', '#ef4444'],
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            cutout: '65%',
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { family: 'Inter', size: 13 } }
                }
            }
        }
    });

    // ── 2. N-Gram Katkı Dağılımı (Radar) ──
    if (data.ngram_contribution) {
        const ctxNgram = document.getElementById('chartNgram').getContext('2d');
        if (ngramChart) ngramChart.destroy();

        const ngLabels = ['Unigram', 'Bigram', 'Trigram', 'Quadgram'];
        const ngValues = [
            data.ngram_contribution.unigram || 0,
            data.ngram_contribution.bigram || 0,
            data.ngram_contribution.trigram || 0,
            data.ngram_contribution.quadgram || 0
        ];
        const ngCorrectValues = [
            (data.correct_ngram_contribution || {}).unigram || 0,
            (data.correct_ngram_contribution || {}).bigram || 0,
            (data.correct_ngram_contribution || {}).trigram || 0,
            (data.correct_ngram_contribution || {}).quadgram || 0
        ];

        ngramChart = new Chart(ctxNgram, {
            type: 'radar',
            data: {
                labels: ngLabels,
                datasets: [
                    {
                        label: 'Tüm Tahminler',
                        data: ngValues,
                        borderColor: '#818cf8',
                        backgroundColor: 'rgba(129, 140, 248, 0.15)',
                        borderWidth: 2,
                        pointBackgroundColor: '#818cf8',
                        pointRadius: 4
                    },
                    {
                        label: 'Doğru Tahminler',
                        data: ngCorrectValues,
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        borderWidth: 2,
                        pointBackgroundColor: '#22c55e',
                        pointRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        ticks: { color: '#64748b', backdropColor: 'transparent' },
                        grid: { color: 'rgba(255,255,255,0.06)' },
                        angleLines: { color: 'rgba(255,255,255,0.08)' },
                        pointLabels: { color: '#94a3b8', font: { size: 12, family: 'Inter' } }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
                    }
                }
            }
        });
    }

    // ── 3. Şık Dağılımı: Tahmin vs Doğru ──
    if (data.predicted_distribution && data.correct_distribution) {
        const ctxDist = document.getElementById('chartDistribution').getContext('2d');
        if (distChart) distChart.destroy();

        const letters = ['A', 'B', 'C', 'D', 'E'];
        distChart = new Chart(ctxDist, {
            type: 'bar',
            data: {
                labels: letters,
                datasets: [
                    {
                        label: 'Model Tahmini',
                        data: letters.map(l => data.predicted_distribution[l] || 0),
                        backgroundColor: 'rgba(129, 140, 248, 0.7)',
                        borderColor: '#818cf8',
                        borderWidth: 1,
                        borderRadius: 6
                    },
                    {
                        label: 'Doğru Cevap',
                        data: letters.map(l => data.correct_distribution[l] || 0),
                        backgroundColor: 'rgba(34, 197, 94, 0.7)',
                        borderColor: '#22c55e',
                        borderWidth: 1,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#64748b', stepSize: 1 },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    x: {
                        ticks: { color: '#94a3b8', font: { size: 14, weight: 'bold' } },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
                    }
                }
            }
        });
    }

    // ── 4. Bar Chart — Soru bazlı ──
    if (data.results && data.results.length > 0) {
        const labels = data.results.map(r => `S${r.id}`);
        const colors = data.results.map(r => r.is_correct ? '#22c55e' : '#ef4444');
        const values = data.results.map(() => 1);

        const ctxBar = document.getElementById('chartBar').getContext('2d');
        if (barChart) barChart.destroy();
        barChart = new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sonuç',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        display: false
                    },
                    x: {
                        ticks: { color: '#64748b', font: { size: 10 } },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const r = data.results[ctx.dataIndex];
                                return `Tahmin: ${r.predicted} | Doğru: ${r.correct} | ${r.is_correct ? '✅' : '❌'}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // ── 5. Tablo ──
    const tbody = document.querySelector('#resultsTable tbody');
    tbody.innerHTML = '';
    (data.results || []).forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${r.id}</td>
            <td class="small">${r.question || '—'}</td>
            <td><span class="badge ${r.predicted === r.correct ? 'bg-success' : 'bg-danger'}">${r.predicted}</span></td>
            <td><span class="badge bg-info">${r.correct}</span></td>
            <td>${r.is_correct ? '✅' : '❌'}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ── YARDIMCI FONKSİYONLAR ──
function formatNumber(num) {
    if (num == null) return '—';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

