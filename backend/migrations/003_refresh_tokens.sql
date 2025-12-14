-- Migration: 003_refresh_tokens.sql
-- Description: Create refresh_tokens table for JWT refresh token management
-- Date: 2025-12-14

-- Create refresh_tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token_hash VARCHAR(256) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    device_info TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Foreign key constraint
    CONSTRAINT fk_refresh_tokens_user 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id 
    ON refresh_tokens(user_id);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash 
    ON refresh_tokens(token_hash);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at 
    ON refresh_tokens(expires_at);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_revoked_at 
    ON refresh_tokens(revoked_at);

-- Composite index for finding valid tokens
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_valid 
    ON refresh_tokens(user_id, expires_at, revoked_at);

-- Add comment
COMMENT ON TABLE refresh_tokens IS 'Stores JWT refresh tokens for session management';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'SHA256 hash of the refresh token (never store raw tokens)';
COMMENT ON COLUMN refresh_tokens.expires_at IS 'Token expiration timestamp (typically 7 days from creation)';
COMMENT ON COLUMN refresh_tokens.revoked_at IS 'Timestamp when token was revoked (NULL if active)';
COMMENT ON COLUMN refresh_tokens.device_info IS 'Device information for security tracking';
COMMENT ON COLUMN refresh_tokens.ip_address IS 'IP address that created the token';
COMMENT ON COLUMN refresh_tokens.user_agent IS 'User agent string for device identification';

-- Function to clean up expired refresh tokens (optional scheduled cleanup)
CREATE OR REPLACE FUNCTION cleanup_expired_refresh_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM refresh_tokens
    WHERE expires_at < NOW() - INTERVAL '1 day'
       OR revoked_at < NOW() - INTERVAL '1 day';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_refresh_tokens IS 'Removes expired or revoked refresh tokens older than 1 day';

