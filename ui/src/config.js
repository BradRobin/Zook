/**
 * Zook Configuration
 * 
 * Centralized configuration for API endpoints and environment settings.
 * Automatically detects protocol (HTTP/HTTPS) and adjusts WebSocket accordingly.
 */

/**
 * Detect API base URL based on current page protocol and location
 * @returns {string} API base URL
 */
function detectApiUrl() {
    // Check if custom API URL is provided via window global
    if (window.ZOOK_API_URL) {
        return window.ZOOK_API_URL;
    }
    
    // Detect from current page location
    const protocol = window.location.protocol; // 'http:' or 'https:'
    const hostname = window.location.hostname;
    
    // In development (localhost), use port 8000
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return `${protocol}//${hostname}:8000`;
    }
    
    // In production, use same hostname (Cloudflare Tunnel or reverse proxy)
    return `${protocol}//${hostname}`;
}

/**
 * Detect WebSocket URL based on API URL
 * @param {string} apiUrl - HTTP API base URL
 * @returns {string} WebSocket URL
 */
function detectWsUrl(apiUrl) {
    // Convert HTTP(S) to WS(S)
    return apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
}

/**
 * Detect environment based on hostname and protocol
 * @returns {string} 'development' or 'production'
 */
function detectEnvironment() {
    const hostname = window.location.hostname;
    
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'development';
    }
    
    return 'production';
}

/**
 * Check if connection should be secure (HTTPS/WSS)
 * @returns {boolean} True if secure connection
 */
function isSecureConnection() {
    return window.location.protocol === 'https:';
}

// Export configuration object
const ZookConfig = {
    // API endpoints
    API_URL: detectApiUrl(),
    WS_URL: detectWsUrl(detectApiUrl()),
    
    // Environment
    ENVIRONMENT: detectEnvironment(),
    IS_SECURE: isSecureConnection(),
    
    // Feature flags
    ENABLE_CAMERA: true,
    ENABLE_SEARCH: true,
    ENABLE_NOTIFICATIONS: false, // TODO: Implement in future
    
    // Streaming settings
    STREAM_FPS: 30,
    STREAM_QUALITY: 0.8, // JPEG quality (0.0 - 1.0)
    
    // Detection settings
    DETECTION_CONFIDENCE_THRESHOLD: 0.90,
    
    // UI settings
    LOG_MAX_ENTRIES: 50,
    SEARCH_DEBOUNCE_MS: 300,
    
    // Logging
    DEBUG: detectEnvironment() === 'development',
    
    /**
     * Log debug message if debug mode is enabled
     * @param {...any} args - Arguments to log
     */
    log(...args) {
        if (this.DEBUG) {
            console.log('[Zook]', ...args);
        }
    },
    
    /**
     * Log info message
     * @param {...any} args - Arguments to log
     */
    info(...args) {
        console.info('[Zook]', ...args);
    },
    
    /**
     * Log warning message
     * @param {...any} args - Arguments to log
     */
    warn(...args) {
        console.warn('[Zook]', ...args);
    },
    
    /**
     * Log error message
     * @param {...any} args - Arguments to log
     */
    error(...args) {
        console.error('[Zook]', ...args);
    }
};

// Log configuration on load
ZookConfig.info('Configuration loaded:', {
    environment: ZookConfig.ENVIRONMENT,
    apiUrl: ZookConfig.API_URL,
    wsUrl: ZookConfig.WS_URL,
    isSecure: ZookConfig.IS_SECURE,
    debug: ZookConfig.DEBUG
});

// Warn if using insecure connection in production
if (ZookConfig.ENVIRONMENT === 'production' && !ZookConfig.IS_SECURE) {
    ZookConfig.warn(
        '⚠️  Using insecure HTTP connection in production! ',
        'Camera access may be blocked by browser. ',
        'Please enable HTTPS.'
    );
}

// Export for use in other scripts
window.ZookConfig = ZookConfig;

// Also support module exports if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ZookConfig;
}

