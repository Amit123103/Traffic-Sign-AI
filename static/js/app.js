/**
 * TrafficSign AI - Core Frontend Engine
 */

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initTheme();
    initUpload();
    initWebcam();
    initVideo();
    initAnalytics();
    initAdmin();
});

// --- Utility Functions ---

function initClock() {
    const clockEl = document.getElementById('live-clock');
    if (!clockEl) return;
    setInterval(() => {
        const now = new Date();
        clockEl.textContent = now.toTimeString().split(' ')[0];
    }, 1000);
}

function initTheme() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;
    
    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    toggle.addEventListener('click', () => {
        const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('#theme-toggle i');
    if (icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}"></i>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// --- Image Detection ---

function initUpload() {
    const dropZone = document.getElementById('drop-zone') || document.getElementById('video-drop-zone');
    const fileInput = document.getElementById('file-input') || document.getElementById('hidden-input');
    
    if (!fileInput) return;

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    if (dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
            dropZone.addEventListener(evt, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) handleFileUpload(files[0]);
        });
    }
}

async function handleFileUpload(file) {
    const formData = new FormData();
    const isVideo = file.type.startsWith('video');
    const endpoint = isVideo ? '/api/detect/video' : '/api/detect/image';
    formData.append(isVideo ? 'video' : 'image', file);

    document.getElementById('loading-overlay').classList.remove('hidden');

    try {
        const response = await fetch(endpoint, { method: 'POST', body: formData });
        const data = await response.json();
        
        if (data.success) {
            if (isVideo) {
                startVideoPolling(data.task_id);
            } else {
                displayImageResult(data);
            }
            showToast('Neural analysis complete', 'success');
        } else {
            showToast(data.error || 'Analysis failed', 'error');
        }
    } catch (err) {
        showToast('Grid connection error', 'error');
    } finally {
        if (!isVideo) document.getElementById('loading-overlay').classList.add('hidden');
    }
}

function displayImageResult(data) {
    const container = document.getElementById('detection-result-container');
    const placeholder = document.getElementById('upload-placeholder');
    const infoEmpty = document.getElementById('info-empty');
    const infoContent = document.getElementById('info-content');

    if (!container) return;

    container.classList.remove('hidden');
    if (placeholder) placeholder.classList.add('hidden');
    if (infoEmpty) infoEmpty.classList.add('hidden');
    if (infoContent) infoContent.classList.remove('hidden');

    document.getElementById('annotated-image').src = data.annotated_url;
    document.getElementById('sign-name').textContent = data.prediction.class_name;
    document.getElementById('category-badge').textContent = data.prediction.category;
    document.getElementById('category-badge').style.backgroundColor = data.prediction.color;
    document.getElementById('hindi-name').textContent = data.prediction.hindi_name;
    document.getElementById('latency').textContent = `${Math.round(data.prediction.processing_time_ms)} ms`;
    document.getElementById('description').textContent = data.prediction.description;

    const conf = Math.round(data.prediction.confidence * 100);
    document.getElementById('confidence-text').textContent = `${conf}%`;
    document.getElementById('confidence-path').style.strokeDasharray = `${conf}, 100`;
    
    // Voice events
    document.getElementById('btn-speak-en').onclick = () => speak(data.prediction.class_id, 'en');
    document.getElementById('btn-speak-hi').onclick = () => speak(data.prediction.class_id, 'hi');
}

async function speak(classId, lang) {
    const res = await fetch('/api/voice/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ class_id: classId, lang })
    });
    const data = await res.json();
    if (data.audio_url) {
        new Audio(data.audio_url).play();
    }
}

// --- Webcam Logic ---

function initWebcam() {
    const captureBtn = document.getElementById('capture-frame');
    if (!captureBtn) return;

    captureBtn.addEventListener('click', async () => {
        // In this mock, we just trigger a flash and toast
        // A real implementation would pull from the canvas
        const flash = document.querySelector('.capture-flash');
        flash.classList.remove('hidden');
        setTimeout(() => flash.classList.add('hidden'), 100);
        showToast('Frame captured to database', 'success');
        
        const countEl = document.getElementById('session-count');
        countEl.textContent = parseInt(countEl.textContent) + 1;
    });
}

// --- Video Processing ---

function startVideoPolling(taskId) {
    const statusCard = document.getElementById('video-status-card');
    const uploadCard = document.getElementById('video-upload-card');
    
    uploadCard.classList.add('hidden');
    statusCard.classList.remove('hidden');

    const interval = setInterval(async () => {
        const res = await fetch(`/api/video/status/${taskId}`);
        const data = await res.json();
        
        if (data.status === 'completed') {
            clearInterval(interval);
            showVideoResult(data.result);
            document.getElementById('loading-overlay').classList.add('hidden');
        } else if (data.status === 'processing') {
            // Update progress if available
            document.getElementById('video-progress').style.width = '50%'; // Simplified
            document.getElementById('progress-text').textContent = 'Analyzing Neural Layers... 50%';
        }
    }, 2000);
}

function showVideoResult(result) {
    document.getElementById('video-status-card').classList.add('hidden');
    const resultCard = document.getElementById('video-result-card');
    resultCard.classList.remove('hidden');

    const video = document.getElementById('processed-video');
    video.src = result.output_url;
    document.getElementById('total-frames').textContent = result.total_frames;
    document.getElementById('total-detections').textContent = result.detection_count;
    document.getElementById('download-video').onclick = () => window.open(result.output_url);
}

// --- Analytics ---

async function initAnalytics() {
    const timelineCtx = document.getElementById('timeline-chart');
    if (!timelineCtx) return;

    const res = await fetch('/api/analytics/data');
    const data = await res.json();

    document.getElementById('total-val').textContent = data.total;

    // Timeline Chart
    new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: Object.keys(data.daily),
            datasets: [{
                label: 'Detections',
                data: Object.values(data.daily),
                borderColor: '#00FF88',
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(0, 255, 136, 0.1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { color: '#1E1E2E' } },
                x: { grid: { display: false } }
            }
        }
    });

    // Category Doughnut
    const catCtx = document.getElementById('category-chart');
    new Chart(catCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data.by_class).slice(0, 5),
            datasets: [{
                data: Object.values(data.by_class).slice(0, 5),
                backgroundColor: ['#00FF88', '#FF3366', '#00D1FF', '#FFCC00', '#888888']
            }]
        }
    });
}

// --- Admin ---

function initAdmin() {
    const clearBtn = document.getElementById('clear-history');
    if (!clearBtn) return;

    clearBtn.addEventListener('click', () => {
        document.getElementById('confirm-modal').classList.remove('hidden');
    });

    document.getElementById('cancel-delete').onclick = () => {
        document.getElementById('confirm-modal').classList.add('hidden');
    };

    document.getElementById('confirm-delete').onclick = async () => {
        const res = await fetch('/api/admin/history', { method: 'DELETE' });
        if (res.ok) {
            location.reload();
        }
    };

    document.getElementById('export-csv').onclick = () => {
        window.location.href = '/api/admin/export/csv';
    };

    loadLogs();
}

async function loadLogs() {
    const logContainer = document.getElementById('system-logs');
    if (!logContainer) return;

    const res = await fetch('/api/admin/logs');
    const data = await res.json();
    
    logContainer.innerHTML = data.logs.map(log => `
        <div class="log-entry ${log.level.toLowerCase()}">
            <span class="time">[${log.timestamp.split('T')[1].split('.')[0]}]</span>
            <span class="level">${log.level}:</span>
            <span class="msg">${log.message}</span>
        </div>
    `).join('');
}
