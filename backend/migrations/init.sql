-- Zook Database Initialization Script
-- PostgreSQL schema for users and sessions tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create index on username for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(500) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    device_info TEXT
);

-- Create indexes on sessions table for faster queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Row Level Security (RLS) policies for user data isolation

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Enable RLS on sessions table
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own data
CREATE POLICY user_read_own_data ON users
    FOR SELECT
    USING (id = current_setting('app.current_user_id', true)::UUID);

-- Policy: Users can only update their own data
CREATE POLICY user_update_own_data ON users
    FOR UPDATE
    USING (id = current_setting('app.current_user_id', true)::UUID);

-- Policy: Users can only read their own sessions
CREATE POLICY session_read_own_data ON sessions
    FOR SELECT
    USING (user_id = current_setting('app.current_user_id', true)::UUID);

-- Policy: Users can only update their own sessions
CREATE POLICY session_update_own_data ON sessions
    FOR UPDATE
    USING (user_id = current_setting('app.current_user_id', true)::UUID);

-- Policy: Users can only delete their own sessions
CREATE POLICY session_delete_own_data ON sessions
    FOR DELETE
    USING (user_id = current_setting('app.current_user_id', true)::UUID);

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    UPDATE sessions
    SET is_active = FALSE
    WHERE expires_at < NOW() AND is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Optional: Create a scheduled job to run cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-sessions', '0 * * * *', 'SELECT cleanup_expired_sessions()');

-- Grant appropriate permissions (adjust for your setup)
-- GRANT SELECT, INSERT, UPDATE ON users TO zook_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON sessions TO zook_app_user;

-- Insert a test user (password: 12345678)
-- Note: This is a bcrypt hash of "12345678" with 12 rounds
INSERT INTO users (id, username, password_hash, created_at)
VALUES (
    uuid_generate_v4(),
    'Brad',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg3Dq',
    NOW()
)
ON CONFLICT (username) DO NOTHING;

-- Verify tables created
\dt

-- Show table structures
\d users
\d sessions

-- Success message
SELECT 'Database schema initialized successfully!' AS status;


