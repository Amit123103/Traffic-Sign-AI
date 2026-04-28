/**
 * TrafficSign AI - Core Frontend Engine
 */

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initTheme();
    initUpload();
    initWebcam();
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
    const video = document.getElementById('webcam-video');
    const canvas = document.getElementById('webcam-canvas');
    const captureBtn = document.getElementById('capture-frame');
    const signNameEl = document.getElementById('live-sign-name');
    const gaugeBar = document.querySelector('.gauge-bar');
    
    if (!video || !canvas) return;

    let stream = null;
    let isNightMode = false;
    let lastPrediction = null;

    // Start Webcam
    async function startCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } } 
            });
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                video.play();
                startInferenceLoop();
            };
        } catch (err) {
            console.error("Camera error:", err);
            showToast("Failed to access camera", "error");
            signNameEl.textContent = "Camera Error";
        }
    }

    // Capture frame and send to server
    async function startInferenceLoop() {
        const context = canvas.getContext('2d');
        
        const runInference = async () => {
            if (video.paused || video.ended) return;

            // Set canvas size to video size
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Convert to blob
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('image', blob, 'webcam.jpg');
                if (isNightMode) formData.append('night_mode', 'true');

                try {
                    const res = await fetch('/api/detect/image', { method: 'POST', body: formData });
                    const data = await res.json();
                    
                    if (data.success && data.prediction) {
                        lastPrediction = data.prediction;
                        updateHUD(data.prediction);
                    }
                } catch (err) {
                    console.error("Inference loop error:", err);
                }
                
                // Continue loop
                setTimeout(runInference, 1000); // 1 FPS for server safety
            }, 'image/jpeg', 0.7);
        };

        runInference();
    }

    function updateHUD(pred) {
        if (!signNameEl) return;
        
        const focusBox = document.querySelector('.focus-box');
        const focusLabel = document.querySelector('.focus-label');

        if (pred.class_id === -1) {
            signNameEl.textContent = "Scanning...";
            gaugeBar.style.width = '0%';
            if (focusBox) focusBox.style.borderColor = 'rgba(0, 255, 255, 0.5)';
            if (focusLabel) focusLabel.textContent = "SCANNING...";
            return;
        }

        signNameEl.textContent = pred.class_name;
        const conf = Math.round(pred.confidence * 100);
        gaugeBar.style.width = `${conf}%`;
        gaugeBar.style.backgroundColor = pred.color;
        
        // Update Focus Box
        if (focusBox) focusBox.style.borderColor = pred.color;
        if (focusLabel) {
            focusLabel.textContent = `${pred.class_name} (${conf}%)`;
            focusLabel.style.backgroundColor = pred.color;
        }

        if (pred.confidence > 0.8) {
            addHistoryItem(pred);
        }
    }

    function addHistoryItem(pred) {
        const list = document.getElementById('session-history-list');
        if (!list) return;
        
        // Only add if different from last item to avoid duplicates
        if (list.firstChild && list.firstChild.dataset.id == pred.class_id) return;

        const item = document.createElement('div');
        item.className = 'history-item';
        item.dataset.id = pred.class_id;
        item.innerHTML = `
            <span class="time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
            <span class="name" style="color: ${pred.color}">${pred.class_name}</span>
        `;
        list.prepend(item);
        if (list.children.length > 5) list.lastChild.remove();
    }

    // Toggle Night Mode
    const nightBtn = document.getElementById('toggle-night-mode');
    if (nightBtn) {
        nightBtn.addEventListener('click', () => {
            isNightMode = !isNightMode;
            nightBtn.classList.toggle('active');
            showToast(`Night Mode ${isNightMode ? 'ON' : 'OFF'}`, 'info');
        });
    }

    // Capture Button
    captureBtn.addEventListener('click', async () => {
        if (!lastPrediction || lastPrediction.class_id === -1) {
            showToast('No sign detected to capture', 'error');
            return;
        }

        const response = await fetch('/api/webcam/capture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lastPrediction)
        });

        if (response.ok) {
            const flash = document.querySelector('.capture-flash');
            if (flash) {
                flash.classList.remove('hidden');
                setTimeout(() => flash.classList.add('hidden'), 100);
            }
            showToast('Frame captured to database', 'success');
            
            const countEl = document.getElementById('session-count');
            if (countEl) countEl.textContent = parseInt(countEl.textContent) + 1;
        }
    });

    startCamera();
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
