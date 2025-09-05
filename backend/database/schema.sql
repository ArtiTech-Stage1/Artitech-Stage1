CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preference_type VARCHAR(50) NOT NULL, -- 'color', 'theme', 'style', 'artist'
    preference_value VARCHAR(100) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_type, preference_value)
);

CREATE TABLE user_mood_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mood VARCHAR(50) NOT NULL,
    intensity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high'
    context TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    total_messages INTEGER DEFAULT 0
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL, -- 'user', 'assistant'
    content TEXT NOT NULL,
    extracted_elements JSONB, -- 
    recommendation_triggered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 
CREATE TABLE recommendation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    message_id UUID REFERENCES chat_messages(id) ON DELETE SET NULL,
    artwork_ids JSONB NOT NULL, -- 
    recommendation_context JSONB, -- 
    user_feedback VARCHAR(20), -- 'liked', 'disliked', 'neutral'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 
CREATE TABLE user_activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- 'login', 'logout', 'chat', 'recommendation', 'preference_update'
    activity_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 
CREATE INDEX idx_users_clerk_user_id ON users(clerk_user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_type ON user_preferences(preference_type);

CREATE INDEX idx_user_mood_history_user_id ON user_mood_history(user_id);
CREATE INDEX idx_user_mood_history_created_at ON user_mood_history(created_at);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_started_at ON chat_sessions(started_at);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

CREATE INDEX idx_recommendation_history_user_id ON recommendation_history(user_id);
CREATE INDEX idx_recommendation_history_created_at ON recommendation_history(created_at);

CREATE INDEX idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX idx_user_activity_logs_activity_type ON user_activity_logs(activity_type);
CREATE INDEX idx_user_activity_logs_created_at ON user_activity_logs(created_at);

-- 
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 
CREATE VIEW user_complete_info AS
SELECT 
    u.id,
    u.clerk_user_id,
    u.email,
    u.username,
    u.first_name,
    u.last_name,
    u.avatar_url,
    u.created_at,
    u.updated_at,
    u.last_login,
    u.is_active,
    COALESCE(
        json_agg(
            json_build_object(
                'type', up.preference_type,
                'value', up.preference_value,
                'weight', up.weight
            )
        ) FILTER (WHERE up.id IS NOT NULL), 
        '[]'::json
    ) as preferences,
    (
        SELECT mood 
        FROM user_mood_history umh 
        WHERE umh.user_id = u.id 
        ORDER BY umh.created_at DESC 
        LIMIT 1
    ) as current_mood
FROM users u
LEFT JOIN user_preferences up ON u.id = up.user_id
GROUP BY u.id;

-- INSERT INTO users (clerk_user_id, email, username, first_name, last_name)
-- VALUES ('clerk_test_123', 'test@example.com', 'testuser', 'Test', 'User');

-- ========================================
-- 艺术品数据库表结构
-- ========================================

-- 启用向量扩展（如果使用pgvector）
-- CREATE EXTENSION IF NOT EXISTS vector;

-- 艺术品主表
CREATE TABLE artworks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    object_id VARCHAR(50) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    object_name VARCHAR(255),
    department VARCHAR(255),
    culture VARCHAR(255),
    period VARCHAR(255),
    artist_display_name TEXT,
    medium TEXT,
    dimensions TEXT,
    classification VARCHAR(255),
    object_date VARCHAR(255),
    general_text_description TEXT,
    url TEXT,

    -- 向量嵌入字段（如果使用pgvector）
    -- title_vector VECTOR(384),
    -- description_vector VECTOR(384),
    -- combined_vector VECTOR(384),

    -- 标签字段
    color_tags TEXT[],
    style_tags TEXT[],
    theme_tags TEXT[],
    emotion_tags TEXT[],

    -- 评分字段
    popularity_score DECIMAL(5,2) DEFAULT 0.0,
    quality_score DECIMAL(5,2) DEFAULT 0.0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 艺术品嵌入向量表（用于存储不同类型的向量）
CREATE TABLE artwork_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    embedding_type VARCHAR(50) NOT NULL, -- 'title', 'description', 'combined'
    embedding_vector TEXT NOT NULL, -- JSON格式存储向量
    model_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 用户与艺术品交互记录表
CREATE TABLE artwork_user_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) NOT NULL, -- 'view', 'like', 'dislike', 'save', 'share'
    interaction_score DECIMAL(3,2) DEFAULT 1.0,
    context JSONB, -- 交互时的上下文信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, artwork_id, interaction_type)
);

-- 艺术品相似度表
CREATE TABLE artwork_similarity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artwork_id_1 UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    artwork_id_2 UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    similarity_score DECIMAL(5,4) NOT NULL,
    similarity_type VARCHAR(50) NOT NULL, -- 'visual', 'semantic', 'style', 'theme'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(artwork_id_1, artwork_id_2, similarity_type)
);

-- 艺术品推荐缓存表
CREATE TABLE artwork_recommendation_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cache_key VARCHAR(255) NOT NULL, -- 基于用户偏好和查询生成的缓存键
    artwork_ids JSONB NOT NULL, -- 推荐的艺术品ID列表
    scores JSONB NOT NULL, -- 对应的评分列表
    query_context JSONB, -- 查询上下文
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, cache_key)
);

-- 创建索引
CREATE INDEX idx_artworks_object_id ON artworks(object_id);
CREATE INDEX idx_artworks_title ON artworks USING gin(to_tsvector('english', title));
CREATE INDEX idx_artworks_description ON artworks USING gin(to_tsvector('english', general_text_description));
CREATE INDEX idx_artworks_artist ON artworks(artist_display_name);
CREATE INDEX idx_artworks_culture ON artworks(culture);
CREATE INDEX idx_artworks_period ON artworks(period);
CREATE INDEX idx_artworks_department ON artworks(department);
CREATE INDEX idx_artworks_classification ON artworks(classification);
CREATE INDEX idx_artworks_color_tags ON artworks USING gin(color_tags);
CREATE INDEX idx_artworks_style_tags ON artworks USING gin(style_tags);
CREATE INDEX idx_artworks_theme_tags ON artworks USING gin(theme_tags);
CREATE INDEX idx_artworks_emotion_tags ON artworks USING gin(emotion_tags);
CREATE INDEX idx_artworks_popularity_score ON artworks(popularity_score DESC);
CREATE INDEX idx_artworks_quality_score ON artworks(quality_score DESC);

CREATE INDEX idx_artwork_embeddings_artwork_id ON artwork_embeddings(artwork_id);
CREATE INDEX idx_artwork_embeddings_type ON artwork_embeddings(embedding_type);

CREATE INDEX idx_artwork_interactions_user_id ON artwork_user_interactions(user_id);
CREATE INDEX idx_artwork_interactions_artwork_id ON artwork_user_interactions(artwork_id);
CREATE INDEX idx_artwork_interactions_type ON artwork_user_interactions(interaction_type);
CREATE INDEX idx_artwork_interactions_created_at ON artwork_user_interactions(created_at);

CREATE INDEX idx_artwork_similarity_artwork1 ON artwork_similarity(artwork_id_1);
CREATE INDEX idx_artwork_similarity_artwork2 ON artwork_similarity(artwork_id_2);
CREATE INDEX idx_artwork_similarity_score ON artwork_similarity(similarity_score DESC);
CREATE INDEX idx_artwork_similarity_type ON artwork_similarity(similarity_type);

CREATE INDEX idx_recommendation_cache_user_id ON artwork_recommendation_cache(user_id);
CREATE INDEX idx_recommendation_cache_key ON artwork_recommendation_cache(cache_key);
CREATE INDEX idx_recommendation_cache_expires ON artwork_recommendation_cache(expires_at);

-- 添加触发器
CREATE TRIGGER update_artworks_updated_at BEFORE UPDATE ON artworks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
