-- 文件名: 0001_initial_schema.sql
-- 描述: 创建项目所需的全部核心表结构（PostgreSQL版）

-- 1. 创建自定义ENUM类型，用于任务状态
CREATE TYPE task_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- 2. 创建 users 表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE users IS '存储系统用户信息';

-- 3. 创建 hotwords 表
CREATE TABLE hotwords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word VARCHAR(255) NOT NULL,
    weight INTEGER NOT NULL DEFAULT 5 CHECK (weight >= 1 AND weight <= 10),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, word)
);
COMMENT ON TABLE hotwords IS '存储用户自定义的热词';
CREATE INDEX idx_hotwords_user_id ON hotwords(user_id);

-- 4. 创建 transcription_tasks 表
CREATE TABLE transcription_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status task_status NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);
COMMENT ON TABLE transcription_tasks IS '记录语音转写任务';
CREATE INDEX idx_tasks_user_id ON transcription_tasks(user_id);
CREATE INDEX idx_tasks_status ON transcription_tasks(status);

-- 5. 创建 transcription_segments 表
CREATE TABLE transcription_segments (
    id BIGSERIAL PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES transcription_tasks(id) ON DELETE CASCADE,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    text TEXT NOT NULL,
    confidence FLOAT
);
COMMENT ON TABLE transcription_segments IS '存储结构化的转写结果分段';
CREATE INDEX idx_segments_task_id ON transcription_segments(task_id); 