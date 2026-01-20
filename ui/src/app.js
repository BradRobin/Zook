// Zook MVP - Vanilla JavaScript Application Logic with WebSocket Streaming

/**
 * CameraStateManager - Manages visual states for camera permission and loading
 * 
 * Handles UI states for:
 * - Requesting camera permission
 * - Permission denied (with retry)
 * - AI model initializing
 * - Connecting to detection service
 * - Ready/Live feed
 */
class CameraStateManager {
    constructor(overlayElement) {
        this.overlay = overlayElement;
        this.spinner = document.getElementById('status-spinner');
        this.icon = document.getElementById('status-icon');
        this.title = document.getElementById('status-title');
        this.message = document.getElementById('status-message');
        this.actionBtn = document.getElementById('status-action');
        
        // Icon elements
        this.iconCamera = document.getElementById('icon-camera');
        this.iconError = document.getElementById('icon-error');
        this.iconSuccess = document.getElementById('icon-success');
        this.iconAi = document.getElementById('icon-ai');
        this.iconWifi = document.getElementById('icon-wifi');
        
        // Current state
        this.currentState = 'hidden';
        
        // Retry callback
        this._onRetry = null;
    }
    
    /**
     * Set the current state of the overlay
     * @param {string} state - One of: 'hidden', 'requesting', 'denied', 'initializing', 'connecting', 'ready', 'error'
     * @param {object} options - Additional options like message, onRetry callback
     */
    setState(state, options = {}) {
        this.currentState = state;
        
        // Remove all state classes
        this.overlay.classList.remove(
            'state-requesting', 'state-denied', 'state-initializing', 
            'state-connecting', 'state-ready', 'state-error'
        );
        
        // Hide all icons
        this._hideAllIcons();
        
        // Reset elements
        this.spinner.classList.add('hidden');
        this.icon.classList.add('hidden');
        this.actionBtn.classList.add('hidden');
        this.title.textContent = '';
        this.message.textContent = '';
        
        switch (state) {
            case 'hidden':
                this.hide();
                break;
            case 'requesting':
                this._showRequestingPermission();
                break;
            case 'denied':
                this._showPermissionDenied(options.onRetry);
                break;
            case 'initializing':
                this._showModelInitializing();
                break;
            case 'connecting':
                this._showConnecting();
                break;
            case 'ready':
                this._showReady();
                break;
            case 'error':
                this._showError(options.message, options.onRetry);
                break;
        }
    }
    
    _hideAllIcons() {
        if (this.iconCamera) this.iconCamera.classList.add('hidden');
        if (this.iconError) this.iconError.classList.add('hidden');
        if (this.iconSuccess) this.iconSuccess.classList.add('hidden');
        if (this.iconAi) this.iconAi.classList.add('hidden');
        if (this.iconWifi) this.iconWifi.classList.add('hidden');
    }
    
    _showIcon(iconElement) {
        if (iconElement) {
            this.icon.classList.remove('hidden');
            iconElement.classList.remove('hidden');
        }
    }
    
    /**
     * Show requesting camera permission state
     */
    showRequestingPermission() {
        this.setState('requesting');
    }
    
    _showRequestingPermission() {
        this.overlay.classList.remove('hidden');
        this.overlay.classList.add('state-requesting');
        
        // Show camera icon with pulse animation
        this._showIcon(this.iconCamera);
        
        // Show spinner
        this.spinner.classList.remove('hidden');
        
        this.title.textContent = 'Requesting Camera Access...';
        this.message.innerHTML = 'Click <strong>"Allow"</strong> when your browser prompts you';
        
        console.log('📷 Camera state: Requesting permission');
    }
    
    /**
     * Show permission denied state with retry option
     */
    showPermissionDenied(onRetry) {
        this.setState('denied', { onRetry });
    }
    
    _showPermissionDenied(onRetry) {
        this.overlay.classList.remove('hidden');
        this.overlay.classList.add('state-denied');
        
        // Show error icon
        this._showIcon(this.iconError);
        
        this.title.textContent = 'Camera Access Denied';
        this.message.innerHTML = `
            Zook needs camera access to detect threats in real-time.
            <br><br>
            <span style="font-size: 0.75rem; opacity: 0.7;">
                Tip: Check your browser's address bar for camera settings
            </span>
        `;
        
        // Show retry button
        if (onRetry) {
            this._onRetry = onRetry;
            this.actionBtn.textContent = 'Try Again';
            this.actionBtn.classList.remove('hidden');
            this.actionBtn.onclick = () => {
                if (this._onRetry) this._onRetry();
            };
        }
        
        console.log('❌ Camera state: Permission denied');
    }
    
    /**
     * Show AI model initializing state
     */
    showModelInitializing() {
        this.setState('initializing');
    }
    
    _showModelInitializing() {
        this.overlay.classList.remove('hidden');
        this.overlay.classList.add('state-initializing');
        
        // Show AI icon
        this._showIcon(this.iconAi);
        
        // Show spinner
        this.spinner.classList.remove('hidden');
        
        this.title.textContent = 'Initializing AI Model...';
        this.message.innerHTML = `
            Loading threat detection engine
            <br>
            <span style="font-size: 0.75rem; opacity: 0.7;">
                First load may take 10-15 seconds
            </span>
        `;
        
        console.log('🤖 Camera state: Model initializing');
    }
    
    /**
     * Show connecting to detection service state
     */
    showConnecting() {
        this.setState('connecting');
    }
    
    _showConnecting() {
        this.overlay.classList.remove('hidden');
        this.overlay.classList.add('state-connecting');
        
        // Show wifi icon
        this._showIcon(this.iconWifi);
        
        // Show spinner
        this.spinner.classList.remove('hidden');
        
        this.title.textContent = 'Connecting to Server...';
        this.message.textContent = 'Establishing secure connection';
        
        console.log('🔌 Camera state: Connecting');
    }
    
    /**
     * Show ready/success state briefly before hiding
     */
    showReady() {
        this.setState('ready');
    }
    
    _showReady() {
        this.overlay.classList.remove('hidden');
        this.overlay.classList.add('state-ready');
        
        // Show success icon
        this._showIcon(this.iconSuccess);
        
        this.title.textContent = 'Connected!';
        this.message.textContent = 'Live detection active';
        
        console.log('✅ Camera state: Ready');
        
        // Auto-hide after brief delay
        setTimeout(() => {
            this.hide();
        }, 1000);
    }
    
    /**
     * Show generic error state
     */
    showError(errorMessage, onRetry) {
        this.setState('error', { message: errorMessage, onRetry });
    }
    
    _showError(errorMessage, onRetry) {
        this.overlay.classList.remove('hidden');
        this.overlay.classList.add('state-error', 'state-denied');
        
        // Show error icon
        this._showIcon(this.iconError);
        
        this.title.textContent = 'Connection Error';
        this.message.textContent = errorMessage || 'Something went wrong. Please try again.';
        
        // Show retry button
        if (onRetry) {
            this._onRetry = onRetry;
            this.actionBtn.textContent = 'Retry';
            this.actionBtn.classList.remove('hidden');
            this.actionBtn.onclick = () => {
                if (this._onRetry) this._onRetry();
            };
        }
        
        console.log('❌ Camera state: Error -', errorMessage);
    }
    
    /**
     * Hide the overlay with fade animation
     */
    hide() {
        this.overlay.classList.add('fade-out');
        
        setTimeout(() => {
            this.overlay.classList.add('hidden');
            this.overlay.classList.remove('fade-out');
            // Remove all state classes
            this.overlay.classList.remove(
                'state-requesting', 'state-denied', 'state-initializing', 
                'state-connecting', 'state-ready', 'state-error'
            );
        }, 300);
        
        this.currentState = 'hidden';
        console.log('👁️ Camera state: Hidden (live feed visible)');
    }
    
    /**
     * Check if overlay is currently visible
     */
    isVisible() {
        return this.currentState !== 'hidden';
    }
}

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
        const demoParam = (window.ZookConfig && window.ZookConfig.DEMO_MODE) ? '&demo=true' : '';
        const wsUrl = this.apiUrl.replace('http://', 'ws://').replace('https://', 'wss://') 
                      + `/ws/stream?token=${this.authToken}${demoParam}`;
        
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
 * RESTDetection - REST API-based detection (5-second intervals)
 * 
 * Alternative to WebSocket streaming. Captures frames every 5 seconds,
 * POSTs to /detect endpoint, and handles responses with visual feedback.
 */
class RESTDetection {
    constructor(apiUrl, authToken) {
        this.apiUrl = apiUrl;
        this.authToken = authToken;
        this.videoElement = null;
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.isScanning = false;
        this.intervalId = null;
        this.captureInterval = 5000; // 5 seconds
        this.frameCount = 0;
        
        // Callbacks
        this.onDetection = null;
        this.onError = null;
        this.onStatusUpdate = null;
        this.onClose = null;
        
        console.log('RESTDetection initialized - 5 second intervals');
    }
    
    async start(videoElement) {
        if (this.isScanning) {
            console.warn('RESTDetection already scanning');
            return;
        }
        
        this.videoElement = videoElement;
        this.isScanning = true;
        
        console.log('🎬 Starting REST API detection (5s intervals)');
        
        // Start interval for capturing and detecting
        this.intervalId = setInterval(() => {
            this.captureAndDetect();
        }, this.captureInterval);
        
        // Capture first frame immediately
        setTimeout(() => this.captureAndDetect(), 100);
    }
    
    async captureFrame() {
        if (!this.videoElement || this.videoElement.readyState !== this.videoElement.HAVE_ENOUGH_DATA) {
            console.warn('Video not ready for capture');
            return null;
        }
        
        // Set canvas size to match video
        this.canvas.width = this.videoElement.videoWidth || 640;
        this.canvas.height = this.videoElement.videoHeight || 640;
        
        // Draw current video frame to canvas
        this.ctx.drawImage(this.videoElement, 0, 0, this.canvas.width, this.canvas.height);
        
        // Convert to blob (JPEG, 80% quality)
        return new Promise((resolve, reject) => {
            this.canvas.toBlob((blob) => {
                if (blob) {
                    resolve(blob);
                } else {
                    reject(new Error('Failed to create blob from canvas'));
                }
            }, 'image/jpeg', 0.8);
        });
    }
    
    async sendDetectionRequest(blob) {
        const formData = new FormData();
        formData.append('image', blob, 'frame.jpg');
        
        try {
            const response = await fetch(`${this.apiUrl}/detect`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    ...(window.ZookConfig && window.ZookConfig.DEMO_MODE ? { 'X-Demo-Mode': 'true' } : {})
                },
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            // Handle offline/error states
            this.handleError(error);
            throw error;
        }
    }
    
    async captureAndDetect() {
        if (!this.isScanning) return;
        
        try {
            const startTime = performance.now();
            
            // Capture frame
            const blob = await this.captureFrame();
            if (!blob) {
                console.warn('No frame captured, skipping detection');
                return;
            }
            
            this.frameCount++;
            console.log(`📸 Frame ${this.frameCount} captured (${(blob.size / 1024).toFixed(1)}KB)`);
            
            // Send to detection API
            const result = await this.sendDetectionRequest(blob);
            
            const processingTime = performance.now() - startTime;
            console.log(`✅ Detection complete in ${processingTime.toFixed(1)}ms`);
            
            // Handle detection response
            this.handleDetectionResponse(result, processingTime);
            
        } catch (error) {
            console.error('Capture and detect error:', error);
            // Continue scanning despite errors
        }
    }
    
    handleDetectionResponse(data, processingTime) {
        // Expected response format:
        // {
        //   "threats_detected": true,
        //   "threats": [
        //     {"type": "knife", "confidence": 0.95, "bbox": {...}}
        //   ],
        //   "processing_time_ms": 45.2
        // }
        
        // Update status
        if (this.onStatusUpdate) {
            this.onStatusUpdate({
                fps: 1000 / this.captureInterval, // Effective FPS
                recording: false, // REST mode doesn't track recording
                processingTime: data.processing_time_ms || processingTime,
                frameNumber: this.frameCount
            });
        }
        
        if (data.threats && data.threats.length > 0) {
            // Filter for knife detections with >=90% confidence
            const knives = data.threats.filter(
                t => t.type === 'knife' && t.confidence >= 0.90
            );
            
            if (knives.length > 0) {
                console.log(`🚨 KNIFE DETECTED! Count: ${knives.length}`);
                
                if (this.onDetection) {
                    this.onDetection(knives, data);
                }
                
                // Trigger red border pulse
                this.pulseRedBorder();
                
                // Log with timestamp
                const timestamp = new Date().toLocaleTimeString();
                knives.forEach(knife => {
                    const confidence = (knife.confidence * 100).toFixed(1);
                    console.log(`[${timestamp}] KNIFE DETECTED! Confidence: ${confidence}%`);
                });
            } else if (data.threats.length > 0) {
                // Threats detected but below 90% threshold
                console.log(`⚠️ ${data.threats.length} threat(s) detected but below 90% confidence threshold`);
            }
        } else {
            console.log('✓ No threats detected');
        }
    }
    
    pulseRedBorder() {
        if (!this.videoElement) return;
        
        const videoElement = this.videoElement;
        videoElement.style.border = '4px solid red';
        videoElement.style.transition = 'border-color 0.3s ease';
        
        setTimeout(() => {
            videoElement.style.border = '1px solid #333';
        }, 1000);
    }
    
    handleError(error) {
        console.error('Detection error:', error);
        
        let errorMessage = `Detection error: ${error.message}`;
        
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            // Network error - backend offline
            errorMessage = 'AI service offline. Retrying in 5 seconds...';
        } else if (error.message.includes('401') || error.message.includes('Unauthorized')) {
            // Authentication error
            errorMessage = 'Authentication failed. Please login again.';
            this.stop(); // Stop scanning on auth failure
        } else if (error.message.includes('500') || error.message.includes('Internal Server Error')) {
            // Server error
            errorMessage = 'Server error. Retrying...';
        }
        
        if (this.onError) {
            this.onError(errorMessage);
        }
    }
    
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        this.isScanning = false;
        console.log('⏹️ REST API detection stopped');
        
        if (this.onClose) {
            this.onClose('Detection stopped');
        }
    }
    
    disconnect() {
        this.stop();
    }
}

/**
 * ZookApp - Main application class
 */
class ZookApp {
    constructor(apiUrl = null) {
        this.isScanning = false;
        this.videoStream = null;
        this.authToken = null;
        this.sessionId = null;
        this.streamingDetection = null;
        this.restDetection = null;
        this.detectionMode = 'websocket'; // 'websocket' or 'rest'
        this.cameraState = null; // Camera state manager for UX feedback
        
        // Use provided API URL or auto-detect
        if (apiUrl) {
            this.apiUrl = apiUrl;
            console.log('Using provided API URL:', this.apiUrl);
        } else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            this.apiUrl = 'http://localhost:8000';
        } else {
            // For remote access, try to get from localStorage or prompt
            this.apiUrl = localStorage.getItem('zook_api_url') || 
                         prompt('Please enter your backend URL (e.g., https://zook.yourdomain.com)', 'https://');
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
        
        // Listen for session expiry events (from TokenManager)
        window.addEventListener('zook:session-expired', () => {
            console.log('Session expired, redirecting to login...');
            this.authToken = null;
            this.sessionId = null;
            this.showLoginModal();
            this.addLogEntry('Session expired. Please login again.', 'warning');
        });
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

        // Search form submission
        document.getElementById('search-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSearch();
        });

        // Privacy links
        document.getElementById('privacy-link')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showPrivacyModal();
        });

        document.getElementById('privacy-dashboard-link')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showPrivacyModal();
        });

        document.getElementById('consent-privacy-link')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showPrivacyModal();
        });

        document.getElementById('accept-privacy')?.addEventListener('click', () => {
            this.hidePrivacyModal();
        });

        document.getElementById('close-privacy')?.addEventListener('click', () => {
            this.hidePrivacyModal();
        });

        document.getElementById('view-privacy')?.addEventListener('click', () => {
            this.showPrivacyModal();
        });

        document.getElementById('download-data')?.addEventListener('click', () => {
            this.downloadUserData();
        });

        document.getElementById('delete-account')?.addEventListener('click', () => {
            this.requestAccountDeletion();
        });

        // Close modal on outside click
        document.getElementById('login-modal').addEventListener('click', (e) => {
            if (e.target.id === 'login-modal') {
                this.hideLoginModal();
            }
        });
    }

    async checkStoredAuth() {
        // Check for stored tokens (legacy format or new format)
        let token = localStorage.getItem('zook_auth_token');
        const sessionId = localStorage.getItem('zook_session_id');
        
        // Use TokenManager if available
        const tokenManager = window.ZookTokenManager;
        
        if (tokenManager && tokenManager.isAuthenticated()) {
            // Check if token needs refresh
            if (tokenManager.needsRefresh()) {
                console.log('Access token expired, attempting refresh...');
                const refreshed = await tokenManager.refreshAccessToken();
                if (!refreshed) {
                    console.log('Token refresh failed, need to re-login');
                    return;
                }
            }
            token = tokenManager.getAccessToken();
        }
        
        if (token && sessionId) {
            // Verify token is still valid
            try {
                const response = await fetch(`${this.apiUrl}/api/verify`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        ...this.getDemoHeaders()
                    }
                });
                
                if (response.ok) {
                    this.authToken = token;
                    this.sessionId = sessionId;
                    console.log('✓ Session restored from stored token');
                    this.showDashboard();
                } else if (response.status === 401 && tokenManager) {
                    // Try to refresh token
                    console.log('Stored token invalid, attempting refresh...');
                    const refreshed = await tokenManager.refreshAccessToken();
                    if (refreshed) {
                        this.authToken = tokenManager.getAccessToken();
                    this.sessionId = sessionId;
                    this.showDashboard();
                } else {
                        this.clearStoredAuth();
                    }
                } else {
                    this.clearStoredAuth();
                }
            } catch (error) {
                console.error('Token verification failed:', error);
                this.clearStoredAuth();
            }
        }
    }
    
    clearStoredAuth() {
        // Clear legacy storage
                localStorage.removeItem('zook_auth_token');
                localStorage.removeItem('zook_session_id');
        
        // Clear TokenManager storage
        if (window.ZookTokenManager) {
            window.ZookTokenManager.clearTokens();
            }
        
        this.authToken = null;
        this.sessionId = null;
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

    getDemoHeaders() {
        if (window.ZookConfig && window.ZookConfig.DEMO_MODE) {
            return { 'X-Demo-Mode': 'true' };
        }
        return {};
    }

    maskDemoValue(value, type = 'generic') {
        if (!(window.ZookConfig && window.ZookConfig.DEMO_MODE)) {
            return value;
        }
        if (type === 'username') {
            return 'demo-user';
        }
        return 'demo';
    }

    getAuthHeaders() {
        /**
         * Get headers with JWT authorization for authenticated requests.
         */
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.authToken}`,
            ...this.getDemoHeaders()
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
                    ...this.getDemoHeaders()
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
            
            // Store tokens using TokenManager (if available)
            if (window.ZookTokenManager) {
                window.ZookTokenManager.storeTokens(data);
            }
            
            // Also store in legacy format for backward compatibility
            this.authToken = data.access_token;
            this.sessionId = data.session_id;
            localStorage.setItem('zook_auth_token', this.authToken);
            localStorage.setItem('zook_session_id', this.sessionId);
            
            console.log('✓ Login successful:', this.maskDemoValue(data.username, 'username'));
            console.log('  Access token expires in:', data.expires_in, 'seconds');
            console.log('  Refresh token expires in:', data.refresh_expires_in, 'seconds');
            
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

        // Initialize camera state manager
        if (!this.cameraState) {
            this.cameraState = new CameraStateManager(
                document.getElementById('video-status-overlay')
            );
        }
        
        // Step 1: Request camera permission
        this.cameraState.showRequestingPermission();

        try {
            // Step 2: Start camera (this triggers browser permission prompt)
            await this.startCamera();
            this.addLogEntry('Camera access granted', 'info');
            
            // Step 3: Show AI model initializing
            this.cameraState.showModelInitializing();
            
            // Step 4: Connect to detection service
            await this.startScanning();
            
            // Step 5: Show ready state briefly, then hide overlay
            this.cameraState.showReady();
            
        } catch (error) {
            console.error('Camera/connection error:', error);
            
            // Determine error type and show appropriate state
            if (error.name === 'NotAllowedError' || 
                error.name === 'PermissionDeniedError' ||
                error.message.includes('denied') ||
                error.message.includes('Permission')) {
                // Camera permission denied
                this.cameraState.showPermissionDenied(() => {
                    // Retry callback - re-attempt the whole flow
                    this.showDashboard();
                });
                this.addLogEntry('Camera access denied', 'error');
            } else if (error.message.includes('WebSocket') || 
                       error.message.includes('connect') ||
                       error.message.includes('network')) {
                // Connection error
                this.cameraState.showError('Unable to connect to detection server', () => {
                    this.showDashboard();
                });
                this.addLogEntry('Server connection failed', 'error');
            } else {
                // Generic error
                this.cameraState.showError(error.message || 'Camera unavailable', () => {
                    this.showDashboard();
                });
                this.addLogEntry('Camera error: ' + error.message, 'error');
            }
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
            
            // Wait for video to be ready
            await new Promise((resolve) => {
                if (videoElement.readyState >= 2) {
                    resolve();
                } else {
                    videoElement.onloadeddata = resolve;
                }
            });
            
        } catch (error) {
            // Preserve the original error for proper state handling
            // NotAllowedError = user denied permission
            // NotFoundError = no camera available
            // NotReadableError = camera in use by another app
            console.error('Camera access error:', error.name, error.message);
            throw error;
        }
    }

    async startScanning(mode = null) {
        if (this.isScanning) return;
        
        // Use provided mode or default to stored/default mode
        if (mode) {
            this.detectionMode = mode;
        }
        
        this.isScanning = true;
        document.getElementById('pause-btn').textContent = 'Pause Scan';
        
        const videoElement = document.getElementById('feed');
        
        if (this.detectionMode === 'rest') {
            // REST API mode - 5 second intervals
            this.addLogEntry('Starting REST API detection (5s intervals)...', 'info');
            
            try {
                // Create REST detection instance
                this.restDetection = new RESTDetection(this.apiUrl, this.authToken);
                
                // Set up callbacks
                this.restDetection.onDetection = (threats, data) => {
                    this.handleThreatDetection(threats, data);
                };
                
                this.restDetection.onStatusUpdate = (status) => {
                    this.updateStreamStatus(status);
                };
                
                this.restDetection.onError = (error) => {
                    this.addLogEntry(`Detection error: ${error}`, 'error');
                };
                
                this.restDetection.onClose = (reason) => {
                    this.addLogEntry(`Detection stopped: ${reason}`, 'info');
                    this.isScanning = false;
                    document.getElementById('pause-btn').textContent = 'Resume Scan';
                    document.getElementById('stream-status')?.classList.add('hidden');
                };
                
                // Start REST detection
                await this.restDetection.start(videoElement);
                
                this.addLogEntry('✅ REST API detection active (5s intervals)', 'info');
                document.getElementById('stream-status')?.classList.remove('hidden');
                
            } catch (error) {
                console.error('Failed to start REST detection:', error);
                this.addLogEntry('Failed to start detection service', 'error');
                this.isScanning = false;
                document.getElementById('pause-btn').textContent = 'Resume Scan';
            }
            
        } else {
            // WebSocket mode - real-time streaming (default)
            this.addLogEntry('Connecting to real-time detection service...', 'info');
            
            // Show connecting state if camera state manager is available
            if (this.cameraState && this.cameraState.isVisible()) {
                this.cameraState.showConnecting();
            }

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
    }

    stopScanning() {
        this.isScanning = false;
        document.getElementById('pause-btn').textContent = 'Resume Scan';
        this.addLogEntry('Scanning paused', 'info');

        if (this.streamingDetection) {
            this.streamingDetection.stopStreaming();
        }
        
        if (this.restDetection) {
            this.restDetection.stop();
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

    async handleSearch() {
        const searchInput = document.getElementById('search-input');
        const prompt = searchInput.value.trim();
        const searchButton = document.querySelector('.search-button');
        
        if (!prompt) {
            return;
        }
        
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '<div class="search-loading">Searching<span class="progress-dots"></span></div>';
        resultsContainer.classList.remove('hidden');
        if (searchButton) {
            searchButton.disabled = true;
            searchButton.classList.add('primary');
        }
        
        try {
            const response = await fetch(`${this.apiUrl}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`,
                    ...this.getDemoHeaders()
                },
                body: JSON.stringify({ prompt })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.displaySearchResults(data);
            
        } catch (error) {
            console.error('Search error:', error);
            resultsContainer.innerHTML = '<div class="search-error">Search failed. Please try again.</div>';
        } finally {
            if (searchButton) {
                searchButton.disabled = false;
            }
        }
    }

    displaySearchResults(data) {
        const resultsContainer = document.getElementById('search-results');
        
        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No clips found — try different wording.</div>';
            return;
        }
        
        let html = `<div class="log-entry" style="margin-bottom: 0.5rem;">Found ${data.results.length} clip(s):</div>`;
        
        data.results.forEach((clip, index) => {
            const timestamp = new Date(clip.start_time).toLocaleString();
            const confidence = clip.yolo_confidence 
                ? `${(clip.yolo_confidence * 100).toFixed(1)}%` 
                : 'N/A';
            
            html += `
                <div class="result-item">
                    <div class="result-header">
                        <span class="result-time">${timestamp}</span>
                        <span class="result-confidence">Conf: ${confidence}</span>
                    </div>
                    <video 
                        class="result-video" 
                        controls 
                        preload="metadata"
                        src="${this.apiUrl}/clips/${clip.id}"
                    >
                        Your browser does not support video playback.
                    </video>
                </div>
            `;
        });
        
        resultsContainer.innerHTML = html;
    }

    showPrivacyModal() {
        document.getElementById('privacy-modal').classList.remove('hidden');
    }

    hidePrivacyModal() {
        document.getElementById('privacy-modal').classList.add('hidden');
    }

    async downloadUserData() {
        // GDPR-style data export
        try {
            const response = await fetch(`${this.apiUrl}/user/data`, {
                headers: this.getAuthHeaders()
            });
            
            if (!response.ok) {
                throw new Error('Data export failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'zook-my-data.json';
            a.click();
            window.URL.revokeObjectURL(url);
            this.addLogEntry('Data export complete', 'info');
        } catch (error) {
            console.error('Data export error:', error);
            this.addLogEntry('Data export failed - feature not yet implemented', 'error');
        }
    }

    async requestAccountDeletion() {
        if (!confirm('Delete your account? This action is irreversible. All recordings and data will be permanently deleted.')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiUrl}/user/delete`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });
            
            if (response.ok) {
                alert('Account deletion request submitted. You will be logged out.');
                localStorage.clear();
                window.location.reload();
            } else {
                throw new Error('Account deletion failed');
            }
        } catch (error) {
            console.error('Account deletion error:', error);
            this.addLogEntry('Account deletion failed - feature not yet implemented', 'error');
        }
    }

    getAuthHeaders() {
        return {
            'Authorization': `Bearer ${this.authToken}`,
            'Content-Type': 'application/json',
            ...this.getDemoHeaders()
        };
    }

    // Cleanup method
    destroy() {
        if (this.streamingDetection) {
            this.streamingDetection.disconnect();
            this.streamingDetection = null;
        }
        
        if (this.restDetection) {
            this.restDetection.disconnect();
            this.restDetection = null;
        }
        
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Use centralized config if available, otherwise fallback to localhost
    const apiUrl = window.ZookConfig ? window.ZookConfig.API_URL : 'http://localhost:8000';
    
    if (window.ZookConfig) {
        console.log('✓ Using ZookConfig:', window.ZookConfig.API_URL);
    } else {
        console.warn('⚠️  ZookConfig not loaded, using default:', apiUrl);
    }
    
    window.zookApp = new ZookApp(apiUrl);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.zookApp) {
        window.zookApp.destroy();
    }
});
