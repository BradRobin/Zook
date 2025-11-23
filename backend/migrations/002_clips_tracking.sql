-- Migration 002: Stream Sessions and Clips Tracking
-- Adds tables for tracking video streaming sessions and recorded clips
-- with validation and cleanup capabilities

-- Create stream_sessions table
CREATE TABLE IF NOT EXISTS stream_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    total_frames INTEGER DEFAULT 0,
    processed_frames INTEGER DEFAULT 0,
    dropped_frames INTEGER DEFAULT 0,
    total_detections INTEGER DEFAULT 0,
    termination_reason VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for stream_sessions
CREATE INDEX IF NOT EXISTS idx_stream_sessions_user_id ON stream_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_stream_sessions_end_time ON stream_sessions(end_time);
CREATE INDEX IF NOT EXISTS idx_stream_sessions_created_at ON stream_sessions(created_at);

-- Create clips table
CREATE TABLE IF NOT EXISTS clips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stream_session_id UUID NOT NULL REFERENCES stream_sessions(id) ON DELETE CASCADE,
    file_path VARCHAR(512) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    file_size_mb FLOAT,
    frame_count INTEGER DEFAULT 0,
    yolo_confidence FLOAT,
    clip_confidence FLOAT,
    is_validated BOOLEAN DEFAULT FALSE,
    validation_attempted_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for clips
CREATE INDEX IF NOT EXISTS idx_clips_stream_session_id ON clips(stream_session_id);
CREATE INDEX IF NOT EXISTS idx_clips_is_validated ON clips(is_validated);
CREATE INDEX IF NOT EXISTS idx_clips_deleted_at ON clips(deleted_at);
CREATE INDEX IF NOT EXISTS idx_clips_created_at ON clips(created_at);

-- Create composite index for cleanup queries (TTL-style)
CREATE INDEX IF NOT EXISTS idx_clips_validation_cleanup 
    ON clips(is_validated, deleted_at, created_at) 
    WHERE deleted_at IS NULL;

-- Create composite index for old session cleanup
CREATE INDEX IF NOT EXISTS idx_stream_sessions_cleanup 
    ON stream_sessions(end_time, created_at) 
    WHERE end_time IS NOT NULL;

-- Add comments for documentation
COMMENT ON TABLE stream_sessions IS 'Tracks video streaming sessions with detection metadata';
COMMENT ON TABLE clips IS 'Tracks recorded video clips with validation status';
COMMENT ON COLUMN clips.yolo_confidence IS 'Initial YOLO detection confidence (0.0-1.0)';
COMMENT ON COLUMN clips.clip_confidence IS 'Secondary CLIP model validation confidence (0.0-1.0)';
COMMENT ON COLUMN clips.is_validated IS 'Whether CLIP validation has been performed';
COMMENT ON COLUMN clips.deleted_at IS 'Soft delete timestamp for false positives';

