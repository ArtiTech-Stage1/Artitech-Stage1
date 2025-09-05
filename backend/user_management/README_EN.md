# User Management System

This is a robust user management system based on Clerk authentication and PostgreSQL database, specifically designed for artwork recommendation applications.

## Features

### 🔐 Authentication System
- **Clerk Integration**: Use Clerk for user authentication and authorization
- **JWT Verification**: Secure token verification mechanism
- **Automatic User Creation**: Automatically create user records on first login

### 👤 User Management
- **User Profiles**: Complete user information management
- **Preference Settings**: Art preferences such as colors, themes, styles
- **Mood Tracking**: User mood history records
- **Activity Logs**: Detailed user behavior tracking

### 💬 Chat System
- **Session Management**: Multi-session support
- **Message History**: Complete conversation records
- **Structured Data**: Extracted emotional and preference elements

### 🎨 Recommendation System
- **Recommendation History**: Record all recommendation results
- **User Feedback**: Collect user evaluations of recommendations
- **Context Records**: Save complete context during recommendations

## Database Architecture

### Core Table Structure

```sql
-- User table
users (id, clerk_user_id, email, username, first_name, last_name, avatar_url, ...)

-- User preferences table
user_preferences (id, user_id, preference_type, preference_value, weight, ...)

-- User mood history table
user_mood_history (id, user_id, mood, intensity, context, created_at)

-- Chat sessions table
chat_sessions (id, user_id, session_name, started_at, ended_at, is_active, ...)

-- Chat messages table
chat_messages (id, session_id, user_id, message_type, content, extracted_elements, ...)

-- Recommendation history table
recommendation_history (id, user_id, session_id, artwork_ids, recommendation_context, ...)

-- User activity logs table
user_activity_logs (id, user_id, activity_type, activity_data, ip_address, ...)
```

## API Endpoints

### Authentication Related
- `POST /api/users/auth/login` - User login/registration
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update user profile

### Preference Management
- `POST /api/users/preferences` - Add user preferences
- `DELETE /api/users/preferences/{type}/{value}` - Delete user preferences
- `POST /api/users/mood` - Update user mood

### Chat Management
- `POST /api/users/sessions` - Create chat session
- `GET /api/users/sessions` - Get user session list
- `GET /api/users/sessions/active` - Get active session
- `POST /api/users/messages` - Add chat message
- `POST /api/users/sessions/{id}/end` - End session

### Recommendation Management
- `POST /api/users/recommendations` - Add recommendation record
- `GET /api/users/recommendations` - Get recommendation history
- `PUT /api/users/recommendations/{id}/feedback` - Update recommendation feedback

### Statistical Information
- `GET /api/users/stats` - Get user statistical information

## Usage Examples

### 1. User Login
```python
# Frontend uses Clerk to get token
headers = {"Authorization": f"Bearer {clerk_token}"}
response = await client.post("/api/users/auth/login", headers=headers)
user_data = response.json()
```

### 2. Add User Preferences
```python
preference_data = {
    "type": "color",
    "value": "blue",
    "weight": 0.8
}
response = await client.post("/api/users/preferences", json=preference_data, headers=headers)
```

### 3. Create Chat Session
```python
session_data = {"session_name": "Art Exploration"}
response = await client.post("/api/users/sessions", json=session_data, headers=headers)
session = response.json()
```

### 4. Add Chat Message
```python
message_data = {
    "session_id": session["id"],
    "message_type": "user",
    "content": "I'm feeling very happy today",
    "extracted_elements": {"mood": "happy", "intensity": "high"},
    "recommendation_triggered": True
}
response = await client.post("/api/users/messages", json=message_data, headers=headers)
```

## Environment Configuration

### Required Environment Variables

```env
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=artech_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_MIN_CONNECTIONS=5
DB_MAX_CONNECTIONS=20

# Clerk Authentication Configuration
CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

## Installation and Setup

### 1. Install Dependencies
```bash
pip install asyncpg pyjwt[crypto] email-validator
```

### 2. Database Initialization
```bash
# Create database
createdb artech_db

# Run SQL script
psql -d artech_db -f database/schema.sql
```

### 3. Configure Clerk
1. Create application in Clerk Dashboard
2. Get Secret Key and Publishable Key
3. Configure environment variables

### 4. Start Application
```bash
python main.py
```

## Architecture Design

### Layered Architecture
```
Routes (API Layer) → Service (Business Logic Layer) → Repository (Data Access Layer) → Database
```

### Main Components
- **Models**: Pydantic data models
- **Repository**: Data access layer, handles database operations
- **Service**: Business logic layer, coordinates various operations
- **Auth**: Authentication middleware and utilities
- **Routes**: API route definitions

### Design Principles
- **Single Responsibility**: Each class and module has clear responsibilities
- **Dependency Injection**: Manage dependencies between components through dependency injection
- **Async Support**: Full support for asynchronous operations
- **Type Safety**: Use Pydantic to ensure data type safety
- **Error Handling**: Comprehensive error handling and logging

## Security Considerations

### Authentication Security
- JWT token verification
- JWKS key rotation support
- Token expiration checking

### Data Security
- SQL injection protection (using parameterized queries)
- Input validation (Pydantic models)
- Encrypted storage of sensitive data

### API Security
- Authentication middleware
- Request limiting
- CORS configuration

## Monitoring and Logging

### Logging
- User activity logs
- API request logs
- Error logs
- Performance logs

### Monitoring Metrics
- User registration/login statistics
- API response times
- Database connection pool status
- Error rate statistics

## Scalability

### Horizontal Scaling
- Stateless design
- Database connection pooling
- Cache support (can add Redis)

### Feature Extension
- Plugin-based architecture
- Event-driven design
- Microservice ready

## Troubleshooting

### Common Issues
1. **Database Connection Failure**: Check database configuration and network connection
2. **Clerk Authentication Failure**: Verify API keys and network access
3. **JWT Verification Failure**: Check token format and expiration time

### Debugging Tips
- Enable detailed logging
- Use database query logs
- Monitor API response times
