# ArtTech Frontend - React应用

基于React和Clerk认证的艺术品推荐前端应用，与后端用户管理系统完整对接。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 环境配置

确保 `.env` 文件中的配置正确：

```env
REACT_APP_CLERK_PUBLISHABLE_KEY=pk_test_cHJlY2lzZS1jb3VnYXItNTIuY2xlcmsuYWNjb3VudHMuZGV2JA
REACT_APP_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm start
```

应用将在 http://localhost:3000 启动

## 🏗️ 项目结构

```
frontend/
├── public/
│   ├── index.html          # HTML模板
│   └── manifest.json       # PWA配置
├── src/
│   ├── components/         # React组件
│   │   ├── Header.js       # 导航头部
│   │   ├── LandingPage.js  # 登录页面
│   │   ├── Dashboard.js    # 仪表板
│   │   ├── Profile.js      # 个人资料
│   │   ├── ChatInterface.js # AI对话界面
│   │   ├── Recommendations.js # 推荐历史
│   │   └── LoadingSpinner.js # 加载组件
│   ├── contexts/
│   │   └── UserContext.js  # 用户状态管理
│   ├── services/
│   │   └── apiService.js   # API服务
│   ├── App.js              # 主应用组件
│   ├── index.js            # 应用入口
│   └── index.css           # 全局样式
├── package.json            # 项目配置
└── .env                    # 环境变量
```

## 🔐 认证流程

### Clerk集成
- 使用 `@clerk/clerk-react` 进行用户认证
- 支持邮箱、社交登录等多种方式
- 自动处理JWT token管理

### 认证状态管理
```javascript
// 在UserContext中管理认证状态
const { getToken, isLoaded, userId } = useAuth();

// 自动设置API请求头
apiService.setAuthToken(token);
```

## 🎨 主要功能

### 1. 用户登录/注册
- **组件**: `LandingPage.js`
- **功能**: Clerk认证界面，自动创建用户记录
- **API**: `POST /api/users/auth/login`

### 2. 个人资料管理
- **组件**: `Profile.js`
- **功能**: 
  - 编辑用户基本信息
  - 管理艺术偏好设置
  - 更新当前心情状态
- **API**: 
  - `PUT /api/users/profile`
  - `POST /api/users/preferences`
  - `POST /api/users/mood`

### 3. AI对话界面
- **组件**: `ChatInterface.js`
- **功能**:
  - 与AI助手实时对话
  - 自动触发艺术品推荐
  - 会话历史管理
- **API**:
  - `POST /api/chat/` (AI对话)
  - `POST /api/recommend/` (获取推荐)
  - `POST /api/users/sessions` (创建会话)

### 4. 推荐历史
- **组件**: `Recommendations.js`
- **功能**:
  - 查看历史推荐记录
  - 提供用户反馈
  - 搜索和过滤功能
- **API**:
  - `GET /api/users/recommendations`
  - `PUT /api/users/recommendations/{id}/feedback`

### 5. 仪表板
- **组件**: `Dashboard.js`
- **功能**:
  - 用户数据概览
  - 快速操作入口
  - 最近活动展示

## 🔧 API集成

### API服务配置
```javascript
// services/apiService.js
class ApiService {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_BASE_URL;
    this.api = axios.create({
      baseURL: this.baseURL,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  setAuthToken(token) {
    this.authToken = token;
  }
}
```

### 主要API调用
```javascript
// 用户登录
await apiService.loginUser();

// 更新资料
await apiService.updateProfile(profileData);

// AI对话
await apiService.chatWithAI(userId, message);

// 获取推荐
await apiService.getArtworkRecommendations(requestData);
```

## 🎯 状态管理

### UserContext
使用React Context管理全局用户状态：

```javascript
const {
  user,              // 用户信息
  preferences,       // 用户偏好
  currentMood,       // 当前心情
  chatSessions,      // 聊天会话
  activeSession,     // 活跃会话
  
  // 操作方法
  updateProfile,
  addPreference,
  updateMood,
  createChatSession,
  sendMessage
} = useUser();
```

## 🎨 样式设计

### 设计系统
- **主色调**: #667eea (紫蓝色)
- **辅助色**: #764ba2 (紫色)
- **成功色**: #10b981 (绿色)
- **警告色**: #f59e0b (橙色)
- **错误色**: #ef4444 (红色)

### 组件样式
使用 `styled-components` 进行样式管理：

```javascript
const Button = styled.button`
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: #5a67d8;
  }
`;
```

## 📱 响应式设计

### 断点设置
- **移动端**: < 768px
- **平板**: 768px - 1024px  
- **桌面**: > 1024px

### 自适应布局
```css
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
```

## 🔍 错误处理

### API错误处理
```javascript
try {
  const result = await apiService.someMethod();
  toast.success('操作成功');
} catch (error) {
  console.error('操作失败:', error);
  toast.error('操作失败，请重试');
}
```

### 加载状态
```javascript
const [loading, setLoading] = useState(false);

// 显示加载组件
if (loading) {
  return <LoadingSpinner text="加载中..." />;
}
```

## 🧪 测试

### 功能测试清单
- [ ] 用户登录/注册流程
- [ ] 个人资料编辑
- [ ] 偏好设置管理
- [ ] AI对话功能
- [ ] 推荐历史查看
- [ ] 反馈提交功能

### 测试命令
```bash
npm test
```

## 🚀 部署

### 构建生产版本
```bash
npm run build
```

### 部署到静态托管
构建后的文件在 `build/` 目录，可部署到：
- Vercel
- Netlify
- GitHub Pages
- AWS S3

## 🔧 开发工具

### 推荐的VS Code扩展
- ES7+ React/Redux/React-Native snippets
- Prettier - Code formatter
- Auto Rename Tag
- Bracket Pair Colorizer

### 调试工具
- React Developer Tools
- Redux DevTools (如果使用Redux)

## 📝 使用说明

### 1. 首次使用
1. 访问应用首页
2. 点击登录/注册
3. 使用邮箱或社交账号登录
4. 完善个人资料和偏好设置

### 2. 日常使用
1. 在仪表板查看概览信息
2. 进入AI对话界面开始聊天
3. 根据心情和偏好获得推荐
4. 在推荐历史中查看和评价推荐

### 3. 个性化设置
1. 在个人资料页面设置偏好
2. 定期更新心情状态
3. 通过反馈改进推荐质量

## 🐛 常见问题

### Q: 登录后页面空白？
A: 检查后端服务是否正常运行，确认API地址配置正确

### Q: 无法获取推荐？
A: 确认已设置用户偏好，检查网络连接和后端服务状态

### Q: 样式显示异常？
A: 清除浏览器缓存，确认CSS文件加载正常

## 📞 技术支持

如遇到问题，请检查：
1. 后端服务是否正常运行
2. 环境变量配置是否正确
3. 网络连接是否正常
4. 浏览器控制台是否有错误信息

---

*这个React前端应用与后端Clerk用户管理系统完美集成，提供了完整的用户体验和功能覆盖。*
