-- AI智能网关数据库完整初始化脚本
-- 确保无乱码问题，包含所有必要的表和数据

-- 1. 设置字符集和排序规则
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection = utf8mb4;
SET character_set_client = utf8mb4;
SET character_set_results = utf8mb4;

-- 2. 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_gateway_config 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 3. 使用数据库
USE ai_gateway_config;

-- 4. 删除所有现有表（按依赖关系顺序）
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS alert_records;
DROP TABLE IF EXISTS alert_rules;
DROP TABLE IF EXISTS policy_templates;
DROP TABLE IF EXISTS access_logs;
DROP TABLE IF EXISTS monitoring_metrics;
DROP TABLE IF EXISTS location_rules;
DROP TABLE IF EXISTS policies;
DROP TABLE IF EXISTS system_configs;
DROP TABLE IF EXISTS proxy_rules;
DROP TABLE IF EXISTS rules;
DROP TABLE IF EXISTS message_matchers;
DROP TABLE IF EXISTS nginx_config;
DROP TABLE IF EXISTS upstream_servers;
DROP TABLE IF EXISTS namespaces;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- 5. 创建8个核心表

-- 5.1 用户表
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar_url VARCHAR(500),
    role VARCHAR(20) DEFAULT 'user',
    status INT DEFAULT 1,
    last_login DATETIME,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5.2 上游服务器表
CREATE TABLE upstream_servers (
    server_id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(100) NOT NULL,
    server_type VARCHAR(50) NOT NULL,
    server_url VARCHAR(500) NOT NULL,
    api_key VARCHAR(500),
    model_config TEXT,
    load_balance_weight INT DEFAULT 1,
    max_connections INT DEFAULT 100,
    timeout_connect INT DEFAULT 30,
    timeout_read INT DEFAULT 300,
    timeout_write INT DEFAULT 300,
    health_check_url VARCHAR(500),
    health_check_interval INT DEFAULT 30,
    status INT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5.3 命名空间表（扩展版）
CREATE TABLE namespaces (
    namespace_id INT AUTO_INCREMENT PRIMARY KEY,
    namespace_code VARCHAR(50) UNIQUE NOT NULL,
    namespace_name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id INT,
    default_upstream_id INT,
    qps_limit INT DEFAULT 100,
    concurrency_limit INT DEFAULT 50,
    quota_daily VARCHAR(50) DEFAULT '10万/天',
    max_request_size VARCHAR(20) DEFAULT '10MB',
    timeout_seconds INT DEFAULT 30,
    quota_warning BOOLEAN DEFAULT FALSE,
    status INT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(user_id),
    FOREIGN KEY (default_upstream_id) REFERENCES upstream_servers(server_id),
    INDEX idx_code (namespace_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5.4 路由规则表（合并了proxy_rules和message_matchers）
CREATE TABLE location_rules (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    path VARCHAR(500) NOT NULL,
    upstream_id INT NOT NULL,
    proxy_cache BOOLEAN DEFAULT FALSE,
    proxy_buffering BOOLEAN DEFAULT FALSE,
    proxy_pass VARCHAR(500),
    is_regex BOOLEAN DEFAULT FALSE,
    limit_req_config JSON,
    sse_support BOOLEAN DEFAULT FALSE,
    chunked_transfer BOOLEAN DEFAULT FALSE,
    -- 报文匹配相关字段
    matcher_type VARCHAR(20) DEFAULT 'path',
    match_field VARCHAR(100),
    match_operator VARCHAR(20),
    match_value TEXT,
    add_headers JSON,
    rewrite_path VARCHAR(200),
    -- 通用字段
    priority INT DEFAULT 100,
    status INT DEFAULT 1,
    created_by INT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (upstream_id) REFERENCES upstream_servers(server_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    INDEX idx_path (path),
    INDEX idx_upstream (upstream_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5.5 策略配置表（合并了rules）
CREATE TABLE policies (
    policy_id INT AUTO_INCREMENT PRIMARY KEY,
    policy_name VARCHAR(100) NOT NULL,
    policy_type VARCHAR(50) NOT NULL,
    description TEXT,
    namespace_id INT,
    namespaces JSON,
    rules JSON NOT NULL,
    rule_type VARCHAR(50),
    rule_config JSON,
    priority INT DEFAULT 100,
    status INT DEFAULT 1,
    created_by INT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (namespace_id) REFERENCES namespaces(namespace_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    INDEX idx_namespace (namespace_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5.6 访问日志表
CREATE TABLE access_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    request_id VARCHAR(100),
    namespace_id INT,
    upstream_id INT,
    client_ip VARCHAR(45),
    user_agent TEXT,
    method VARCHAR(10),
    path VARCHAR(500),
    status_code INT,
    response_time INT,
    request_size INT,
    response_size INT,
    input_tokens INT,
    output_tokens INT,
    api_key VARCHAR(100),
    error_message TEXT,
    timestamp DATETIME NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (namespace_id) REFERENCES namespaces(namespace_id),
    FOREIGN KEY (upstream_id) REFERENCES upstream_servers(server_id),
    INDEX idx_namespace_timestamp (namespace_id, timestamp),
    INDEX idx_status_code (status_code),
    INDEX idx_client_ip (client_ip),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5.7 系统配置表（合并了nginx_config）
CREATE TABLE system_configs (
    config_id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    config_type VARCHAR(50) DEFAULT 'string',
    config_category VARCHAR(50) DEFAULT 'general',
    config_priority INT DEFAULT 100,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    updated_by INT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(user_id),
    INDEX idx_category (config_category),
    INDEX idx_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5.8 监控指标表
CREATE TABLE monitoring_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    namespace_id INT,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSON,
    timestamp DATETIME NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (namespace_id) REFERENCES namespaces(namespace_id),
    INDEX idx_namespace_timestamp (namespace_id, timestamp),
    INDEX idx_metric_name (metric_name),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 插入默认数据

-- 6.1 插入默认用户
INSERT INTO users (username, email, password_hash, full_name, role) VALUES 
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4.5.6.7', '系统管理员', 'admin');

-- 6.2 插入示例上游服务器
INSERT INTO upstream_servers (server_name, server_type, server_url, api_key, load_balance_weight, max_connections, health_check_url, health_check_interval) VALUES
('mock-llm-server', 'custom', 'http://localhost:8003', '', 1, 100, '/health', 30),
('openai-prod', 'openai', 'https://api.openai.com/v1', 'sk-xxx', 1, 100, '/health', 30);

-- 6.3 插入示例命名空间
INSERT INTO namespaces (namespace_code, namespace_name, description, owner_id, qps_limit, concurrency_limit, quota_daily, max_request_size, timeout_seconds) VALUES
('wechat', '微信渠道', '微信小程序和公众号渠道', 1, 100, 50, '10万/天', '10MB', 30),
('alipay', '支付宝渠道', '支付宝小程序和H5渠道', 1, 100, 50, '10万/天', '10MB', 30),
('web', 'Web渠道', 'Web浏览器渠道', 1, 100, 50, '10万/天', '10MB', 30);

-- 6.4 插入示例路由规则
INSERT INTO location_rules (path, upstream_id, proxy_pass, limit_req_config, sse_support, chunked_transfer, priority, created_by) VALUES
('/v1/chat/completions', 1, 'http://mock-llm-server/v1/chat/completions', '{"enabled": true, "zone": "llm", "burst": 20, "nodelay": true}', TRUE, TRUE, 100, 1),
('/v1/completions', 1, 'http://mock-llm-server/v1/completions', '{"enabled": true, "zone": "llm", "burst": 20, "nodelay": true}', TRUE, TRUE, 100, 1);

-- 6.5 插入示例策略
INSERT INTO policies (policy_name, policy_type, rule_type, description, namespace_id, rules, priority, created_by) VALUES
('基础限流策略', 'rate_limit', 'rate_limit', '适用于一般场景的基础限流策略', 1, '{"rate_limit": {"requests_per_minute": 60, "burst": 10}}', 100, 1),
('高并发策略', 'concurrent', 'concurrent', '适用于高并发场景的策略', 1, '{"concurrent_limit": {"max_concurrent": 100, "queue_size": 50}}', 100, 1),
('Token限制策略', 'token_limit', 'token_limit', '基于Token数量的限制策略', 1, '{"token_limit": {"max_tokens_per_hour": 100000, "max_tokens_per_request": 4000}}', 100, 1);

-- 6.6 插入系统配置
INSERT INTO system_configs (config_key, config_value, config_type, config_category, description) VALUES
('system.name', 'AI智能网关', 'string', 'general', '系统名称'),
('system.version', '2.0.0', 'string', 'general', '系统版本'),
('monitoring.retention_days', '30', 'number', 'monitoring', '监控数据保留天数'),
('logging.level', 'INFO', 'string', 'logging', '日志级别'),
('security.jwt_secret', 'your-secret-key', 'string', 'security', 'JWT密钥'),
('security.session_timeout', '3600', 'number', 'security', '会话超时时间（秒）'),
-- Nginx配置
('nginx.user', 'nginx', 'string', 'nginx', 'Nginx运行用户'),
('nginx.worker_processes', 'auto', 'string', 'nginx', 'Nginx工作进程数'),
('nginx.error_log', '/var/log/nginx/error.log notice', 'string', 'nginx', 'Nginx错误日志'),
('nginx.pid', '/var/run/nginx.pid', 'string', 'nginx', 'Nginx PID文件'),
('nginx.events.use', 'epoll', 'string', 'nginx', 'Nginx事件模型'),
('nginx.events.worker_connections', '4096', 'number', 'nginx', 'Nginx工作连接数'),
('nginx.events.multi_accept', 'true', 'boolean', 'nginx', 'Nginx多路接受'),
('nginx.http.client_max_body_size', '256M', 'string', 'nginx', 'Nginx最大请求体大小'),
('nginx.http.proxy_http_version', '1.1', 'string', 'nginx', 'Nginx代理HTTP版本'),
('nginx.http.proxy_buffers', '4 256K', 'string', 'nginx', 'Nginx代理缓冲区'),
('nginx.http.proxy_buffer_size', '256K', 'string', 'nginx', 'Nginx代理缓冲区大小'),
('nginx.http.proxy_busy_buffers_size', '512K', 'string', 'nginx', 'Nginx代理忙缓冲区大小'),
('nginx.http.proxy_connect_timeout', '900s', 'string', 'nginx', 'Nginx代理连接超时'),
('nginx.http.proxy_read_timeout', '1800s', 'string', 'nginx', 'Nginx代理读取超时'),
('nginx.http.proxy_send_timeout', '1800s', 'string', 'nginx', 'Nginx代理发送超时'),
('nginx.http.keepalive_timeout', '180s', 'string', 'nginx', 'Nginx保持连接超时'),
('nginx.http.keepalive_requests', '100', 'number', 'nginx', 'Nginx保持连接请求数'),
('nginx.http.access_log', '/var/log/nginx/access.log main', 'string', 'nginx', 'Nginx访问日志'),
('nginx.http.log_format', 'main', 'string', 'nginx', 'Nginx日志格式'),
('nginx.http.sendfile', 'true', 'boolean', 'nginx', 'Nginx发送文件'),
('nginx.http.tcp_nopush', 'true', 'boolean', 'nginx', 'Nginx TCP推送'),
('nginx.http.tcp_nodelay', 'true', 'boolean', 'nginx', 'Nginx TCP延迟'),
('nginx.server.listen', '8080', 'number', 'nginx', 'Nginx服务器监听端口'),
('nginx.server.server_name', 'localhost', 'string', 'nginx', 'Nginx服务器名称'),
('nginx.limit_req.enabled', 'true', 'boolean', 'nginx', 'Nginx限流启用'),
('nginx.limit_req.zone', 'llm:10m', 'string', 'nginx', 'Nginx限流区域'),
('nginx.limit_req.rate', '30r/s', 'string', 'nginx', 'Nginx限流速率');

-- 7. 显示初始化结果
SELECT 'Database initialization completed successfully!' as message;
SELECT 'Created tables:' as info;
SELECT TABLE_NAME as table_name FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'ai_gateway_config' 
ORDER BY TABLE_NAME;

SELECT 'Namespaces data:' as info;
SELECT namespace_id, namespace_code, namespace_name, description FROM namespaces;

SELECT 'System configs data:' as info;
SELECT config_key, config_value, description FROM system_configs LIMIT 5;
