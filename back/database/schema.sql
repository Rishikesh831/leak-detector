-- Leak Detector Database Schema
-- PostgreSQL 12+

-- Create database (run this first manually)
-- CREATE DATABASE leak_detector;
-- \c leak_detector;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- Table: uploads
-- Stores metadata about uploaded CSV files
-- ========================================
CREATE TABLE uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rows_count INTEGER NOT NULL,
    columns_count INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'uploaded', -- uploaded, processing, completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster lookups
CREATE INDEX idx_uploads_timestamp ON uploads(upload_timestamp DESC);
CREATE INDEX idx_uploads_status ON uploads(status);

-- ========================================
-- Table: anomalies
-- Stores detected anomalies from ML processing
-- ========================================
CREATE TABLE anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    row_index INTEGER NOT NULL, -- Original row in CSV
    anomaly_score DECIMAL(10, 8) NOT NULL, -- 0.0 to 1.0
    severity VARCHAR(20) DEFAULT 'medium', -- high, medium, low
    status VARCHAR(50) DEFAULT 'unreviewed', -- unreviewed, reviewed, actioned
    timestamp TIMESTAMP WITH TIME ZONE,
    feature_values JSONB, -- Store all feature values as JSON
    shap_values JSONB, -- Cached SHAP explanations
    model_prediction VARCHAR(50), -- Classification result if any
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_anomalies_upload_id ON anomalies(upload_id);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);
CREATE INDEX idx_anomalies_status ON anomalies(status);
CREATE INDEX idx_anomalies_score ON anomalies(anomaly_score DESC);
CREATE INDEX idx_anomalies_timestamp ON anomalies(timestamp DESC);

-- GIN index for JSON queries
CREATE INDEX idx_anomalies_feature_values ON anomalies USING GIN (feature_values);
CREATE INDEX idx_anomalies_shap_values ON anomalies USING GIN (shap_values);

-- ========================================
-- Table: actions
-- Stores user actions taken on anomalies
-- ========================================
CREATE TABLE actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anomaly_id UUID NOT NULL REFERENCES anomalies(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL, -- mark_reviewed, create_work_order, export
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) -- Optional: user identifier
);

-- Index for lookup by anomaly
CREATE INDEX idx_actions_anomaly_id ON actions(anomaly_id);
CREATE INDEX idx_actions_type ON actions(action_type);
CREATE INDEX idx_actions_created_at ON actions(created_at DESC);

-- ========================================
-- Table: processing_jobs
-- Tracks ML processing job status
-- ========================================
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'queued', -- queued, processing, completed, failed
    progress INTEGER DEFAULT 0, -- 0-100
    anomalies_found INTEGER DEFAULT 0,
    processing_time DECIMAL(10, 2), -- seconds
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_jobs_upload_id ON processing_jobs(upload_id);
CREATE INDEX idx_jobs_status ON processing_jobs(status);
CREATE INDEX idx_jobs_created_at ON processing_jobs(created_at DESC);

-- ========================================
-- Triggers for updated_at
-- ========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_uploads_updated_at BEFORE UPDATE ON uploads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_anomalies_updated_at BEFORE UPDATE ON anomalies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON processing_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- Views for dashboard metrics
-- ========================================
CREATE OR REPLACE VIEW dashboard_metrics AS
SELECT
    COUNT(DISTINCT u.id) as total_uploads,
    COALESCE(SUM(u.rows_count), 0) as total_samples,
    COUNT(a.id) as anomalies_detected,
    COALESCE(AVG(a.anomaly_score), 0) as avg_anomaly_score,
    MAX(u.upload_timestamp) as last_updated,
    COUNT(CASE WHEN a.severity = 'high' THEN 1 END) as high_severity_count,
    COUNT(CASE WHEN a.severity = 'medium' THEN 1 END) as medium_severity_count,
    COUNT(CASE WHEN a.severity = 'low' THEN 1 END) as low_severity_count,
    COUNT(CASE WHEN a.status = 'unreviewed' THEN 1 END) as unreviewed_count
FROM uploads u
LEFT JOIN anomalies a ON u.id = a.upload_id;

-- ========================================
-- Sample data for testing (optional)
-- ========================================
-- Uncomment to insert test data
-- INSERT INTO uploads (filename, rows_count, columns_count, file_path, status)
-- VALUES ('test_data.csv', 1000, 25, '/data/uploads/test_data.csv', 'completed');
