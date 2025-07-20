-- Create scene_breakdowns table for scene-by-scene breakdown visualization
CREATE TABLE IF NOT EXISTS scene_breakdowns (
    id SERIAL PRIMARY KEY,
    scene_id VARCHAR(36) UNIQUE NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    act_number INTEGER NOT NULL CHECK (act_number BETWEEN 1 AND 3),
    chapter_number INTEGER,
    scene_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    scene_type VARCHAR(50) DEFAULT 'dialogue',
    location VARCHAR(255) NOT NULL,
    time_of_day VARCHAR(50) NOT NULL,
    duration_minutes DECIMAL(4,2) NOT NULL,
    slug_line VARCHAR(500) NOT NULL,
    synopsis TEXT,
    script_notes TEXT,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'complete', 'review', 'approved')),
    completion_percentage DECIMAL(5,2) DEFAULT 0.0 CHECK (completion_percentage BETWEEN 0 AND 100),
    characters JSONB DEFAULT '[]',
    assets JSONB DEFAULT '[]',
    story_beats JSONB DEFAULT '[]',
    story_circle_position INTEGER CHECK (story_circle_position BETWEEN 1 AND 8),
    conflict_level INTEGER DEFAULT 1 CHECK (conflict_level BETWEEN 1 AND 5),
    stakes_level INTEGER DEFAULT 1 CHECK (stakes_level BETWEEN 1 AND 5),
    color_palette JSONB DEFAULT '[]',
    mood_tags JSONB DEFAULT '[]',
    camera_angles JSONB DEFAULT '[]',
    canvas_position JSONB,
    connections JSONB DEFAULT '[]',
    thumbnail_url VARCHAR(500),
    color_indicator VARCHAR(7) DEFAULT '#3b82f6',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    
    -- Indexes for performance
    INDEX idx_project_scenes (project_id, act_number, chapter_number),
    INDEX idx_scene_status (status),
    INDEX idx_story_circle (story_circle_position),
    INDEX idx_updated_at (updated_at)
);

-- Create indexes for JSONB fields (GIN indexes for querying)
CREATE INDEX IF NOT EXISTS idx_scene_characters ON scene_breakdowns USING GIN (characters);
CREATE INDEX IF NOT EXISTS idx_scene_assets ON scene_breakdowns USING GIN (assets);
CREATE INDEX IF NOT EXISTS idx_scene_story_beats ON scene_breakdowns USING GIN (story_beats);
CREATE INDEX IF NOT EXISTS idx_scene_connections ON scene_breakdowns USING GIN (connections);

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_scene_breakdowns_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    NEW.version = NEW.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_scene_breakdowns_updated_at
    BEFORE UPDATE ON scene_breakdowns
    FOR EACH ROW
    EXECUTE FUNCTION update_scene_breakdowns_updated_at();

-- Insert sample data for testing
INSERT INTO scene_breakdowns (
    scene_id, project_id, act_number, scene_number, title, description,
    scene_type, location, time_of_day, duration_minutes, slug_line, synopsis,
    status, completion_percentage, characters, assets, story_beats, color_indicator
) VALUES 
(
    'scene_001', 'test_project_001', 1, 1, 'Opening Scene', 'The protagonist is introduced in their ordinary world',
    'dialogue', 'Small Town Cafe', 'Morning', 3.5, 'INT. SMALL TOWN CAFE - MORNING',
    'Sarah sits alone at the counter, nursing a cold cup of coffee as the morning rush swirls around her.',
    'complete', 95.0, 
    '[{"character_id": "char_001", "character_name": "Sarah", "role_in_scene": "Protagonist", "screen_time": 3.5, "emotions": ["melancholy", "nostalgic"]}]',
    '[{"asset_id": "asset_001", "asset_type": "prop", "asset_name": "Coffee Cup", "quantity": 1}]',
    '[{"beat_id": "beat_001", "beat_type": "opening", "description": "Introduce protagonist in ordinary world", "importance": 5}]',
    '#8b5cf6'
),
(
    'scene_002', 'test_project_001', 1, 2, 'The Call to Adventure', 'A mysterious stranger arrives with life-changing news',
    'action', 'Small Town Cafe', 'Morning', 4.0, 'INT. SMALL TOWN CAFE - CONTINUOUS',
    'A stranger enters the cafe and approaches Sarah with an urgent message that will change everything.',
    'in_progress', 75.0,
    '[{"character_id": "char_001", "character_name": "Sarah", "role_in_scene": "Protagonist", "screen_time": 3.0}, {"character_id": "char_002", "character_name": "The Stranger", "role_in_scene": "Messenger", "screen_time": 1.0}]',
    '[{"asset_id": "asset_002", "asset_type": "prop", "asset_name": "Mysterious Letter", "quantity": 1}]',
    '[{"beat_id": "beat_002", "beat_type": "inciting_incident", "description": "Call to adventure arrives", "importance": 5}]',
    '#ef4444'
),
(
    'scene_003', 'test_project_001', 1, 3, 'Refusal of the Call', 'Sarah initially rejects the adventure',
    'dialogue', 'Sarah\'s Apartment', 'Evening', 2.5, 'INT. SARAH\'S APARTMENT - EVENING',
    'Sarah sits in her apartment, staring at the mysterious letter, torn between safety and the unknown.',
    'draft', 25.0,
    '[{"character_id": "char_001", "character_name": "Sarah", "role_in_scene": "Protagonist", "screen_time": 2.5}]',
    '[]',
    '[{"beat_id": "beat_003", "beat_type": "setup", "description": "Protagonist refuses the call", "importance": 3}]',
    '#f59e0b'
);