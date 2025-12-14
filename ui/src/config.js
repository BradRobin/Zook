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
    
    // Token settings
    TOKEN_REFRESH_THRESHOLD_MS: 60000, // Refresh 1 minute before expiry
    ACCESS_TOKEN_KEY: 'zook_access_token',
    REFRESH_TOKEN_KEY: 'zook_refresh_token',
    TOKEN_EXPIRY_KEY: 'zook_token_expiry',
    
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

/**
 * Token Manager - Handles JWT token storage and automatic refresh
 */
class TokenManager {
    constructor(config) {
        this.config = config;
        this.refreshTimer = null;
    }
    
    /**
     * Store tokens from login response
     * @param {Object} tokenData - Login response with access_token, refresh_token, expires_in
     */
    storeTokens(tokenData) {
        localStorage.setItem(this.config.ACCESS_TOKEN_KEY, tokenData.access_token);
        localStorage.setItem(this.config.REFRESH_TOKEN_KEY, tokenData.refresh_token);
        
        // Calculate and store expiry time
        const expiryTime = Date.now() + (tokenData.expires_in * 1000);
        localStorage.setItem(this.config.TOKEN_EXPIRY_KEY, expiryTime.toString());
        
        this.config.log('Tokens stored, expires at:', new Date(expiryTime).toISOString());
        
        // Schedule auto-refresh
        this.scheduleRefresh(tokenData.expires_in * 1000);
    }
    
    /**
     * Get the current access token
     * @returns {string|null} Access token or null
     */
    getAccessToken() {
        return localStorage.getItem(this.config.ACCESS_TOKEN_KEY);
    }
    
    /**
     * Get the current refresh token
     * @returns {string|null} Refresh token or null
     */
    getRefreshToken() {
        return localStorage.getItem(this.config.REFRESH_TOKEN_KEY);
    }
    
    /**
     * Check if access token is expired or about to expire
     * @returns {boolean} True if token needs refresh
     */
    needsRefresh() {
        const expiry = localStorage.getItem(this.config.TOKEN_EXPIRY_KEY);
        if (!expiry) return true;
        
        const expiryTime = parseInt(expiry);
        const threshold = this.config.TOKEN_REFRESH_THRESHOLD_MS;
        
        return Date.now() >= (expiryTime - threshold);
    }
    
    /**
     * Check if user is authenticated (has valid tokens)
     * @returns {boolean} True if authenticated
     */
    isAuthenticated() {
        return this.getAccessToken() !== null && this.getRefreshToken() !== null;
    }
    
    /**
     * Clear all tokens (logout)
     */
    clearTokens() {
        localStorage.removeItem(this.config.ACCESS_TOKEN_KEY);
        localStorage.removeItem(this.config.REFRESH_TOKEN_KEY);
        localStorage.removeItem(this.config.TOKEN_EXPIRY_KEY);
        
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
            this.refreshTimer = null;
        }
        
        this.config.log('Tokens cleared');
    }
    
    /**
     * Schedule automatic token refresh
     * @param {number} expiresInMs - Token expiry in milliseconds
     */
    scheduleRefresh(expiresInMs) {
        // Clear existing timer
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
        }
        
        // Schedule refresh before token expires
        const refreshTime = expiresInMs - this.config.TOKEN_REFRESH_THRESHOLD_MS;
        
        if (refreshTime > 0) {
            this.config.log(`Token refresh scheduled in ${refreshTime / 1000}s`);
            
            this.refreshTimer = setTimeout(() => {
                this.refreshAccessToken();
            }, refreshTime);
        }
    }
    
    /**
     * Refresh the access token using refresh token
     * @returns {Promise<boolean>} True if refresh successful
     */
    async refreshAccessToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            this.config.warn('No refresh token available');
            return false;
        }
        
        try {
            this.config.log('Refreshing access token...');
            
            const response = await fetch(`${this.config.API_URL}/api/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Store new access token
                localStorage.setItem(this.config.ACCESS_TOKEN_KEY, data.access_token);
                
                // Update expiry
                const expiryTime = Date.now() + (data.expires_in * 1000);
                localStorage.setItem(this.config.TOKEN_EXPIRY_KEY, expiryTime.toString());
                
                // Schedule next refresh
                this.scheduleRefresh(data.expires_in * 1000);
                
                this.config.log('Access token refreshed successfully');
                return true;
            } else if (response.status === 401) {
                // Refresh token expired or invalid - need to re-login
                this.config.warn('Refresh token expired, clearing tokens');
                this.clearTokens();
                
                // Trigger re-login event
                window.dispatchEvent(new CustomEvent('zook:session-expired'));
                return false;
            } else {
                this.config.error('Token refresh failed:', response.status);
                return false;
            }
        } catch (error) {
            this.config.error('Token refresh error:', error);
            return false;
        }
    }
    
    /**
     * Make an authenticated API request with automatic token refresh
     * @param {string} url - Request URL
     * @param {Object} options - Fetch options
     * @returns {Promise<Response>} Fetch response
     */
    async authenticatedFetch(url, options = {}) {
        // Check if token needs refresh
        if (this.needsRefresh()) {
            await this.refreshAccessToken();
        }
        
        // Add authorization header
        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${this.getAccessToken()}`
        };
        
        const response = await fetch(url, { ...options, headers });
        
        // If unauthorized, try to refresh and retry once
        if (response.status === 401) {
            const refreshed = await this.refreshAccessToken();
            if (refreshed) {
                headers['Authorization'] = `Bearer ${this.getAccessToken()}`;
                return fetch(url, { ...options, headers });
            }
        }
        
        return response;
    }
}

// Create global token manager instance
const ZookTokenManager = new TokenManager(ZookConfig);

// Export for use in other scripts
window.ZookConfig = ZookConfig;
window.ZookTokenManager = ZookTokenManager;

// Also support module exports if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ZookConfig, ZookTokenManager };
}

