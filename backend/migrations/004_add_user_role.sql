-- Add role column to users table for basic RBAC
ALTER TABLE users
ADD COLUMN IF NOT EXISTS role VARCHAR(50) NOT NULL DEFAULT 'user';

-- Backfill any existing rows with null role (safety for older data)
UPDATE users
SET role = 'user'
WHERE role IS NULL;

-- Add index for role-based filtering
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
