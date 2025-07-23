# 用户管理系统

这是一个基于 Clerk 认证和 PostgreSQL 数据库的强健用户管理系统，专为艺术品推荐应用设计。

## 功能特性

### 🔐 认证系统
- **Clerk 集成**：使用 Clerk 进行用户认证和授权
- **JWT 验证**：安全的 token 验证机制
- **自动用户创建**：首次登录时自动创建用户记录

### 👤 用户管理
- **用户资料**：完整的用户信息管理
- **偏好设置**：颜色、主题、风格等艺术偏好
- **情绪跟踪**：用户情绪历史记录
- **活动日志**：详细的用户行为追踪

### 💬 聊天系统
- **会话管理**：多会话支持
- **消息历史**：完整的对话记录
- **结构化数据**：提取的情感和偏好元素

### 🎨 推荐系统
- **推荐历史**：记录所有推荐结果
- **用户反馈**：收集用户对推荐的评价
- **上下文记录**：保存推荐时的完整上下文

## 数据库架构

### 核心表结构

```sql
-- 用户表
users (id, clerk_user_id, email, username, first_name, last_name, avatar_url, ...)

-- 用户偏好表
user_preferences (id, user_id, preference_type, preference_value, weight, ...)

-- 用户情绪历史表
user_mood_history (id, user_id, mood, intensity, context, created_at)

-- 聊天会话表
chat_sessions (id, user_id, session_name, started_at, ended_at, is_active, ...)

-- 聊天消息表
chat_messages (id, session_id, user_id, message_type, content, extracted_elements, ...)

-- 推荐历史表
recommendation_history (id, user_id, session_id, artwork_ids, recommendation_context, ...)

-- 用户活动日志表
user_activity_logs (id, user_id, activity_type, activity_data, ip_address, ...)
```

## API 端点

### 认证相关
- `POST /api/users/auth/login` - 用户登录/注册
- `GET /api/users/profile` - 获取用户资料
- `PUT /api/users/profile` - 更新用户资料

### 偏好管理
- `POST /api/users/preferences` - 添加用户偏好
- `DELETE /api/users/preferences/{type}/{value}` - 删除用户偏好
- `POST /api/users/mood` - 更新用户情绪

### 聊天管理
- `POST /api/users/sessions` - 创建聊天会话
- `GET /api/users/sessions` - 获取用户会话列表
- `GET /api/users/sessions/active` - 获取活跃会话
- `POST /api/users/messages` - 添加聊天消息
- `POST /api/users/sessions/{id}/end` - 结束会话

### 推荐管理
- `POST /api/users/recommendations` - 添加推荐记录
- `GET /api/users/recommendations` - 获取推荐历史
- `PUT /api/users/recommendations/{id}/feedback` - 更新推荐反馈

### 统计信息
- `GET /api/users/stats` - 获取用户统计信息

## 使用示例

### 1. 用户登录
```python
# 前端使用 Clerk 获取 token
headers = {"Authorization": f"Bearer {clerk_token}"}
response = await client.post("/api/users/auth/login", headers=headers)
user_data = response.json()
```

### 2. 添加用户偏好
```python
preference_data = {
    "type": "color",
    "value": "blue",
    "weight": 0.8
}
response = await client.post("/api/users/preferences", json=preference_data, headers=headers)
```

### 3. 创建聊天会话
```python
session_data = {"session_name": "艺术探索"}
response = await client.post("/api/users/sessions", json=session_data, headers=headers)
session = response.json()
```

### 4. 添加聊天消息
```python
message_data = {
    "session_id": session["id"],
    "message_type": "user",
    "content": "我今天感觉很开心",
    "extracted_elements": {"mood": "happy", "intensity": "high"},
    "recommendation_triggered": True
}
response = await client.post("/api/users/messages", json=message_data, headers=headers)
```

## 环境配置

### 必需的环境变量

```env
# PostgreSQL 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=artech_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_MIN_CONNECTIONS=5
DB_MAX_CONNECTIONS=20

# Clerk 认证配置
CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

## 安装和设置

### 1. 安装依赖
```bash
pip install asyncpg pyjwt[crypto] email-validator
```

### 2. 数据库初始化
```bash
# 创建数据库
createdb artech_db

# 运行 SQL 脚本
psql -d artech_db -f database/schema.sql
```

### 3. 配置 Clerk
1. 在 Clerk Dashboard 中创建应用
2. 获取 Secret Key 和 Publishable Key
3. 配置环境变量

### 4. 启动应用
```bash
python main.py
```

## 架构设计

### 分层架构
```
Routes (API层) → Service (业务逻辑层) → Repository (数据访问层) → Database
```

### 主要组件
- **Models**: Pydantic 数据模型
- **Repository**: 数据访问层，处理数据库操作
- **Service**: 业务逻辑层，协调各种操作
- **Auth**: 认证中间件和工具
- **Routes**: API 路由定义

### 设计原则
- **单一职责**：每个类和模块都有明确的职责
- **依赖注入**：通过依赖注入管理组件间的依赖关系
- **异步支持**：全面支持异步操作
- **类型安全**：使用 Pydantic 确保数据类型安全
- **错误处理**：完善的错误处理和日志记录

## 安全考虑

### 认证安全
- JWT token 验证
- JWKS 密钥轮换支持
- Token 过期检查

### 数据安全
- SQL 注入防护（使用参数化查询）
- 输入验证（Pydantic 模型）
- 敏感数据加密存储

### API 安全
- 认证中间件
- 请求限制
- CORS 配置

## 监控和日志

### 日志记录
- 用户活动日志
- API 请求日志
- 错误日志
- 性能日志

### 监控指标
- 用户注册/登录统计
- API 响应时间
- 数据库连接池状态
- 错误率统计

## 扩展性

### 水平扩展
- 无状态设计
- 数据库连接池
- 缓存支持（可添加 Redis）

### 功能扩展
- 插件化架构
- 事件驱动设计
- 微服务就绪

## 故障排除

### 常见问题
1. **数据库连接失败**：检查数据库配置和网络连接
2. **Clerk 认证失败**：验证 API 密钥和网络访问
3. **JWT 验证失败**：检查 token 格式和过期时间

### 调试技巧
- 启用详细日志记录
- 使用数据库查询日志
- 监控 API 响应时间
