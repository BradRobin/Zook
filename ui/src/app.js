// Zook MVP - Vanilla JavaScript Application Logic

class ZookApp {
    constructor() {
        this.isScanning = false;
        this.detectionInterval = null;
        this.videoStream = null;
        this.authToken = null;
        
        // Auto-detect API URL based on environment
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            this.apiUrl = 'http://localhost:8080';
        } else {
            // For remote access, try to get from localStorage or prompt
            this.apiUrl = localStorage.getItem('zook_api_url') || 
                         prompt('Please enter your backend ngrok URL (e.g., https://xxxxx.ngrok-free.dev)', 'https://');
            if (this.apiUrl && this.apiUrl !== 'https://') {
                localStorage.setItem('zook_api_url', this.apiUrl);
            }
        }
        
        console.log('Using API URL:', this.apiUrl);
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkStoredAuth();
    }

    bindEvents() {
        // Landing page scan button
        document.getElementById('scan-btn').addEventListener('click', () => {
            this.showLoginModal();
        });

        // Login form submission
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAuth();
        });

        // Cancel login
        document.getElementById('cancel-btn').addEventListener('click', () => {
            this.hideLoginModal();
        });

        // Dashboard controls
        document.getElementById('pause-btn').addEventListener('click', () => {
            this.toggleScanning();
        });

        document.getElementById('settings-btn').addEventListener('click', () => {
            this.toggleSettings();
        });

        document.getElementById('close-settings').addEventListener('click', () => {
            this.hideSettings();
        });

        // Close modal on outside click
        document.getElementById('login-modal').addEventListener('click', (e) => {
            if (e.target.id === 'login-modal') {
                this.hideLoginModal();
            }
        });
    }

    checkStoredAuth() {
        const token = localStorage.getItem('zook_auth_token');
        if (token) {
            this.authToken = token;
            this.showDashboard();
        }
    }

    showLoginModal() {
        document.getElementById('login-modal').classList.remove('hidden');
        document.getElementById('username').focus();
    }

    hideLoginModal() {
        document.getElementById('login-modal').classList.add('hidden');
        document.getElementById('login-form').reset();
        this.hideError();
    }

    showError(message) {
        const errorEl = document.getElementById('auth-error');
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }

    hideError() {
        document.getElementById('auth-error').classList.add('hidden');
    }

    async handleAuth() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const consent = document.getElementById('consent').checked;

        if (!username || !password) {
            this.showError('Username and password are required');
            return;
        }

        if (!consent) {
            this.showError('You must consent to camera processing');
            return;
        }

        try {
            const response = await fetch(`${this.apiUrl}/api/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    token: ''
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.text();
            
            // Store the success message as pseudo-token for MVP
            this.authToken = result;
            localStorage.setItem('zook_auth_token', this.authToken);
            
            this.hideLoginModal();
            this.showDashboard();

        } catch (error) {
            console.error('Auth error:', error);
            console.error('Error details:', {
                message: error.message,
                name: error.name,
                stack: error.stack
            });
            
            // Map common errors to user-friendly messages
            let errorMessage = 'Authentication failed: ' + error.message;
            if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Cannot connect to server. Please check if the backend is running.';
            } else if (error.message.includes('HTTP 500')) {
                errorMessage = 'Server error. Please try again.';
            } else if (error.message.includes('HTTP 400')) {
                errorMessage = 'Invalid credentials or request format.';
            } else if (error.message.includes('HTTP 401')) {
                errorMessage = 'Invalid username or password.';
            }
            
            this.showError(errorMessage);
        }
    }

    async showDashboard() {
        // Hide landing page, show dashboard
        document.getElementById('landing-page').classList.add('hidden');
        document.getElementById('dashboard-page').classList.remove('hidden');

        try {
            await this.startCamera();
            this.startScanning();
        } catch (error) {
            console.error('Camera error:', error);
            this.addLogEntry('Camera access denied or unavailable', 'error');
        }
    }

    async startCamera() {
        try {
            this.videoStream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });
            
            const videoElement = document.getElementById('feed');
            videoElement.srcObject = this.videoStream;
            
            this.addLogEntry('Camera feed active', 'info');
        } catch (error) {
            throw new Error('Camera access denied or unavailable');
        }
    }

    startScanning() {
        this.isScanning = true;
        document.getElementById('pause-btn').textContent = 'Pause Scan';
        this.addLogEntry('Scanning started...', 'info');

        // Start detection simulation every 5 seconds
        this.detectionInterval = setInterval(() => {
            this.simulateDetection();
        }, 5000);
    }

    stopScanning() {
        this.isScanning = false;
        document.getElementById('pause-btn').textContent = 'Resume Scan';
        this.addLogEntry('Scanning paused', 'info');

        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
    }

    toggleScanning() {
        if (this.isScanning) {
            this.stopScanning();
        } else {
            this.startScanning();
        }
    }

    async simulateDetection() {
        if (!this.isScanning) return;

        try {
            // Capture frame from video
            const canvas = document.createElement('canvas');
            const video = document.getElementById('feed');
            const ctx = canvas.getContext('2d');
            
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            ctx.drawImage(video, 0, 0);

            // Convert to blob for API call
            const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8));
            
            // Simulate API call to detection endpoint
            const formData = new FormData();
            formData.append('image', blob, 'frame.jpg');

            try {
                const response = await fetch('http://localhost:8000/detect', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const result = await response.json();
                    if (result.threats && result.threats.length > 0) {
                        this.handleThreatDetection(result.threats);
                    }
                }
            } catch (apiError) {
                // Fallback to random simulation for MVP
                this.simulateRandomDetection();
            }

        } catch (error) {
            console.error('Detection error:', error);
            // Fallback to random simulation
            this.simulateRandomDetection();
        }
    }

    simulateRandomDetection() {
        // 10% chance of random threat detection for MVP
        if (Math.random() < 0.1) {
            const threats = [{
                type: 'knife',
                confidence: Math.floor(Math.random() * 20) + 80, // 80-99%
                timestamp: new Date()
            }];
            this.handleThreatDetection(threats);
        }
    }

    handleThreatDetection(threats) {
        threats.forEach(threat => {
            const timestamp = threat.timestamp || new Date();
            const timeStr = timestamp.toLocaleTimeString();
            const confidence = threat.confidence || Math.floor(Math.random() * 20) + 80;
            
            this.addLogEntry(`Threat spotted at ${timeStr} - Confidence: ${confidence}%`, 'threat');
            
            // Trigger visual alert
            this.triggerThreatAlert();
        });
    }

    triggerThreatAlert() {
        const videoSection = document.querySelector('.video-section');
        videoSection.classList.add('threat-detected');
        
        // Remove animation class after animation completes
        setTimeout(() => {
            videoSection.classList.remove('threat-detected');
        }, 2000);
    }

    addLogEntry(message, type = 'info') {
        const logsContainer = document.getElementById('status-logs');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.textContent = message;
        
        logsContainer.appendChild(logEntry);
        
        // Keep only last 10 log entries
        while (logsContainer.children.length > 10) {
            logsContainer.removeChild(logsContainer.firstChild);
        }
        
        // Scroll to bottom
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    toggleSettings() {
        const drawer = document.getElementById('settings-drawer');
        drawer.classList.toggle('hidden');
        drawer.classList.toggle('active');
    }

    hideSettings() {
        const drawer = document.getElementById('settings-drawer');
        drawer.classList.add('hidden');
        drawer.classList.remove('active');
    }

    // Cleanup method
    destroy() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
        }
        
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.zookApp = new ZookApp();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.zookApp) {
        window.zookApp.destroy();
    }
});
