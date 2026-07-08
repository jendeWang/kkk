-- PostgreSQL 数据库初始化脚本
-- IoT Platform

-- 启用 UUID 支持
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建性能监控扩展
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 创建专用表空间（可选，提高性能）
-- CREATE TABLESPACE iot_data LOCATION '/var/lib/postgresql/data/iot';

-- 设置默认编码和 locale
ALTER DATABASE iot_platform SET client_encoding = 'UTF8';
ALTER DATABASE iot_platform SET timezone = 'UTC';

-- 创建性能优化函数
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 记录初始化完成
DO $$
BEGIN
    RAISE NOTICE 'IoT Platform database initialized successfully';
END $$;
