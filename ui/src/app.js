// Zook MVP - Vanilla JavaScript Application Logic with WebSocket Streaming

/**
 * StreamingDetection - Real-time video streaming with WebSocket
 * 
 * Handles continuous frame streaming at 30fps to backend,
 * receives real-time detection results via WebSocket,
 * manages recording state and session lifecycle.
 */
class StreamingDetection {
    constructor(apiUrl, authToken) {
        this.apiUrl = apiUrl;
        this.authToken = authToken;
        this.websocket = null;
        this.videoElement = null;
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.targetFPS = 30;  // Capture at 30fps, backend downsamples to 15fps
        this.frameInterval = 1000 / this.targetFPS;
        this.lastFrameTime = 0;
        this.isStreaming = false;
        this.frameCount = 0;
        this.sessionId = null;
        this.isRecording = false;
        this.actualFPS = 0;
        this.idleMinutes = 0;
        
        // Callbacks
        this.onDetection = null;
        this.onStatusUpdate = null;
        this.onError = null;
        this.onClose = null;
    }
    
    async connect(videoElement) {
        this.videoElement = videoElement;
        
        // Convert http to ws protocol
        const wsUrl = this.apiUrl.replace('http://', 'ws://').replace('https://', 'wss://') 
                      + `/ws/stream?token=${this.authToken}`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        return new Promise((resolve, reject) => {
            try {
                this.websocket = new WebSocket(wsUrl);
                
                this.websocket.onopen = () => {
                    console.log('✅ WebSocket connected');
                    resolve();
                };
                
                this.websocket.onmessage = (event) => {
                    this.handleMessage(event.data);
                };
                
                this.websocket.onerror = (error) => {
                    console.error('❌ WebSocket error:', error);
                    if (this.onError) {
                        this.onError('WebSocket connection error');
                    }
                    reject(error);
                };
                
                this.websocket.onclose = (event) => {
                    console.log('WebSocket closed:', event.code, event.reason);
                    this.isStreaming = false;
                    
                    if (this.onClose) {
                        let reason = 'Connection closed';
                        if (event.code === 4001) {
                            reason = 'Authentication failed';
                        } else if (event.code === 1000) {
                            reason = 'Idle timeout (5 minutes without detection)';
                        }
                        this.onClose(reason);
                    }
                };
                
            } catch (error) {
                console.error('Failed to create WebSocket:', error);
                reject(error);
            }
        });
    }
    
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            
            // Welcome message on connect
            if (message.type === 'connected') {
                console.log('📩 Welcome:', message.message);
                this.sessionId = message.session_id;
                this.startStreaming();
                return;
            }
            
            // Detection result
            if (message.threats !== undefined) {
                this.frameCount++;
                this.actualFPS = message.fps || 0;
                this.isRecording = message.recording || false;
                this.idleMinutes = message.idle_minutes || 0;
                
                // Update status
                if (this.onStatusUpdate) {
                    this.onStatusUpdate({
                        fps: this.actualFPS,
                        recording: this.isRecording,
                        idleMinutes: this.idleMinutes,
                        processingTime: message.processing_time_ms,
                        queueSize: message.queue_size,
                        frameNumber: message.frame_number
                    });
                }
                
                // Handle threats
                if (message.threats && message.threats.length > 0 && this.onDetection) {
                    this.onDetection(message.threats, message);
                }
            }
            
            // Error message
            if (message.error) {
                console.error('Server error:', message.error);
                if (this.onError) {
                    this.onError(message.error);
                }
            }
            
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    
    startStreaming() {
        if (this.isStreaming) return;
        
        this.isStreaming = true;
        console.log('🎬 Starting frame streaming at', this.targetFPS, 'FPS');
        this.streamFrames();
    }
    
    async streamFrames() {
        if (!this.isStreaming || !this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            return;
        }
        
        const now = performance.now();
        
        // Check if it's time to send next frame (30 FPS = 33ms between frames)
        if (now - this.lastFrameTime >= this.frameInterval) {
            // Capture frame from video
            if (this.videoElement && this.videoElement.readyState === this.videoElement.HAVE_ENOUGH_DATA) {
                this.canvas.width = 640;
                this.canvas.height = 640;
                this.ctx.drawImage(this.videoElement, 0, 0, 640, 640);
                
                // Convert to blob (JPEG, 80% quality)
                this.canvas.toBlob((blob) => {
                    if (blob && this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                        // Send frame as binary data
                        blob.arrayBuffer().then(buffer => {
                            this.websocket.send(buffer);
                        });
                    }
                }, 'image/jpeg', 0.8);
            }
            
            this.lastFrameTime = now;
        }
        
        // Schedule next frame using requestAnimationFrame for smooth performance
        requestAnimationFrame(() => this.streamFrames());
    }
    
    stopStreaming() {
        this.isStreaming = false;
        console.log('⏸️ Streaming paused');
    }
    
    disconnect() {
        this.isStreaming = false;
        
        if (this.websocket) {
            this.websocket.close(1000, 'User disconnect');
            this.websocket = null;
        }
        
        console.log('🔌 WebSocket disconnected');
    }
}

/**
 * ZookApp - Main application class
 */
class ZookApp {
    constructor() {
        this.isScanning = false;
        this.videoStream = null;
        this.authToken = null;
        this.sessionId = null;
        this.streamingDetection = null;
        
        // Auto-detect API URL based on environment
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            this.apiUrl = 'http://localhost:8000';
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
        this.addStatusIndicators();
    }
    
    addStatusIndicators() {
        // Add FPS counter and recording indicator to the page
        const videoSection = document.querySelector('.video-section');
        if (videoSection && !document.getElementById('stream-status')) {
            const statusHTML = `
                <div id="stream-status" class="stream-status hidden">
                    <div class="status-item">
                        <span class="status-label">FPS:</span>
                        <span id="fps-counter" class="status-value">0.0</span>
                    </div>
                    <div class="status-item recording-indicator hidden" id="recording-indicator">
                        <span class="recording-dot"></span>
                        <span class="status-label">Recording</span>
                    </div>
                    <div class="status-item hidden" id="idle-indicator">
                        <span class="status-label">Idle:</span>
                        <span id="idle-counter" class="status-value">0.0m</span>
                    </div>
                </div>
            `;
            videoSection.insertAdjacentHTML('beforeend', statusHTML);
        }
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

    async checkStoredAuth() {
        const token = localStorage.getItem('zook_auth_token');
        const sessionId = localStorage.getItem('zook_session_id');
        
        if (token && sessionId) {
            // Verify token is still valid
            try {
                const response = await fetch(`${this.apiUrl}/api/verify`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    this.authToken = token;
                    this.sessionId = sessionId;
                    this.showDashboard();
                } else {
                    // Token expired or invalid, clear storage
                    localStorage.removeItem('zook_auth_token');
                    localStorage.removeItem('zook_session_id');
                }
            } catch (error) {
                console.error('Token verification failed:', error);
                localStorage.removeItem('zook_auth_token');
                localStorage.removeItem('zook_session_id');
            }
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

    getAuthHeaders() {
        /**
         * Get headers with JWT authorization for authenticated requests.
         */
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.authToken}`
        };
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
                    password: password
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Store JWT token and session_id
            this.authToken = data.access_token;
            this.sessionId = data.session_id;
            localStorage.setItem('zook_auth_token', this.authToken);
            localStorage.setItem('zook_session_id', this.sessionId);
            
            console.log('Login successful:', data.username);
            
            this.hideLoginModal();
            this.showDashboard();

        } catch (error) {
            console.error('Auth error:', error);
            
            // Map common errors to user-friendly messages
            let errorMessage = 'Authentication failed: ' + error.message;
            if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Cannot connect to server. Please check if the backend is running on port 8000.';
            } else if (error.message.includes('HTTP 500') || error.message.includes('500')) {
                errorMessage = 'Server error. Please try again.';
            } else if (error.message.includes('HTTP 400') || error.message.includes('400')) {
                errorMessage = 'Invalid credentials or request format.';
            } else if (error.message.includes('HTTP 401') || error.message.includes('401') || error.message.includes('Invalid username')) {
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
            await this.startScanning();
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

    async startScanning() {
        if (this.isScanning) return;
        
        this.isScanning = true;
        document.getElementById('pause-btn').textContent = 'Pause Scan';
        this.addLogEntry('Connecting to real-time detection service...', 'info');

        try {
            // Create streaming detection instance
            this.streamingDetection = new StreamingDetection(this.apiUrl, this.authToken);
            
            // Set up callbacks
            this.streamingDetection.onDetection = (threats, data) => {
                this.handleThreatDetection(threats, data);
            };
            
            this.streamingDetection.onStatusUpdate = (status) => {
                this.updateStreamStatus(status);
            };
            
            this.streamingDetection.onError = (error) => {
                this.addLogEntry(`Stream error: ${error}`, 'error');
            };
            
            this.streamingDetection.onClose = (reason) => {
                this.addLogEntry(`Stream closed: ${reason}`, 'info');
                this.isScanning = false;
                document.getElementById('pause-btn').textContent = 'Resume Scan';
                
                // Hide status indicators
                document.getElementById('stream-status')?.classList.add('hidden');
            };
            
            // Connect to WebSocket
            const videoElement = document.getElementById('feed');
            await this.streamingDetection.connect(videoElement);
            
            this.addLogEntry('✅ Real-time streaming active (15 FPS)', 'info');
            
            // Show status indicators
            document.getElementById('stream-status')?.classList.remove('hidden');
            
        } catch (error) {
            console.error('Failed to start streaming:', error);
            this.addLogEntry('Failed to connect to detection service', 'error');
            this.isScanning = false;
            document.getElementById('pause-btn').textContent = 'Resume Scan';
        }
    }

    stopScanning() {
        this.isScanning = false;
        document.getElementById('pause-btn').textContent = 'Resume Scan';
        this.addLogEntry('Streaming paused', 'info');

        if (this.streamingDetection) {
            this.streamingDetection.stopStreaming();
        }
        
        // Hide status indicators
        document.getElementById('stream-status')?.classList.add('hidden');
    }

    toggleScanning() {
        if (this.isScanning) {
            this.stopScanning();
        } else {
            this.startScanning();
        }
    }

    updateStreamStatus(status) {
        // Update FPS counter
        const fpsCounter = document.getElementById('fps-counter');
        if (fpsCounter) {
            fpsCounter.textContent = status.fps.toFixed(1);
        }
        
        // Update recording indicator
        const recordingIndicator = document.getElementById('recording-indicator');
        if (recordingIndicator) {
            if (status.recording) {
                recordingIndicator.classList.remove('hidden');
            } else {
                recordingIndicator.classList.add('hidden');
            }
        }
        
        // Update idle counter
        const idleIndicator = document.getElementById('idle-indicator');
        const idleCounter = document.getElementById('idle-counter');
        if (idleIndicator && idleCounter) {
            if (status.idleMinutes > 0) {
                idleIndicator.classList.remove('hidden');
                idleCounter.textContent = status.idleMinutes.toFixed(1) + 'm';
            } else {
                idleIndicator.classList.add('hidden');
            }
        }
    }

    handleThreatDetection(threats, data) {
        threats.forEach(threat => {
            const timestamp = new Date();
            const timeStr = timestamp.toLocaleTimeString();
            const confidence = Math.round((threat.confidence || 0) * 100);
            
            this.addLogEntry(
                `🚨 ${threat.type.toUpperCase()} detected at ${timeStr} - Confidence: ${confidence}%`, 
                'threat'
            );
            
            // Log processing time if available
            if (data && data.processing_time_ms) {
                console.log(`Processing time: ${data.processing_time_ms.toFixed(1)}ms`);
            }
            
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
        if (this.streamingDetection) {
            this.streamingDetection.disconnect();
            this.streamingDetection = null;
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
