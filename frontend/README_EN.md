# ArtTech Frontend - React Application

React-based artwork recommendation frontend application with Clerk authentication, fully integrated with the backend user management system.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Configuration

Ensure the configuration in `.env` file is correct:

```env
REACT_APP_CLERK_PUBLISHABLE_KEY=pk_test_cHJlY2lzZS1jb3VnYXItNTIuY2xlcmsuYWNjb3VudHMuZGV2JA
REACT_APP_API_BASE_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm start
```

The application will start at http://localhost:3000

## 🏗️ Project Structure

```
frontend/
├── public/
│   ├── index.html          # HTML template
│   └── manifest.json       # PWA configuration
├── src/
│   ├── components/         # React components
│   │   ├── Header.js       # Navigation header
│   │   ├── LandingPage.js  # Landing page
│   │   ├── Dashboard.js    # Dashboard
│   │   ├── Profile.js      # User profile
│   │   ├── ChatInterface.js # AI chat interface
│   │   ├── Recommendations.js # Recommendation history
│   │   └── LoadingSpinner.js # Loading component
│   ├── contexts/
│   │   └── UserContext.js  # User state management
│   ├── services/
│   │   └── apiService.js   # API service
│   ├── App.js              # Main application component
│   ├── index.js            # Application entry point
│   └── index.css           # Global styles
├── package.json            # Project configuration
└── .env                    # Environment variables
```

## 🔐 Authentication Flow

### Clerk Integration
- Use `@clerk/clerk-react` for user authentication
- Support multiple login methods including email and social login
- Automatic JWT token management

### Authentication State Management
```javascript
// Manage authentication state in UserContext
const { getToken, isLoaded, userId } = useAuth();

// Automatically set API request headers
apiService.setAuthToken(token);
```

## 🎨 Main Features

### 1. User Login/Registration
- **Component**: `LandingPage.js`
- **Features**: Clerk authentication interface, automatic user record creation
- **API**: `POST /api/users/auth/login`

### 2. Profile Management
- **Component**: `Profile.js`
- **Features**: 
  - Edit user basic information
  - Manage art preference settings
  - Update current mood state
- **APIs**: 
  - `PUT /api/users/profile`
  - `POST /api/users/preferences`
  - `POST /api/users/mood`

### 3. AI Chat Interface
- **Component**: `ChatInterface.js`
- **Features**:
  - Real-time conversation with AI assistant
  - Automatic artwork recommendation triggering
  - Session history management
- **APIs**:
  - `POST /api/chat/` (AI conversation)
  - `POST /api/recommend/` (Get recommendations)
  - `POST /api/users/sessions` (Create session)

### 4. Recommendation History
- **Component**: `Recommendations.js`
- **Features**:
  - View historical recommendation records
  - Provide user feedback
  - Search and filter functionality
- **APIs**:
  - `GET /api/users/recommendations`
  - `PUT /api/users/recommendations/{id}/feedback`

### 5. Dashboard
- **Component**: `Dashboard.js`
- **Features**:
  - User data overview
  - Quick action access
  - Recent activity display

## 🔧 API Integration

### API Service Configuration
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

### Main API Calls
```javascript
// User login
await apiService.loginUser();

// Update profile
await apiService.updateProfile(profileData);

// AI conversation
await apiService.chatWithAI(userId, message);

// Get recommendations
await apiService.getArtworkRecommendations(requestData);
```

## 🎯 State Management

### UserContext
Use React Context to manage global user state:

```javascript
const {
  user,              // User information
  preferences,       // User preferences
  currentMood,       // Current mood
  chatSessions,      // Chat sessions
  activeSession,     // Active session
  
  // Operation methods
  updateProfile,
  addPreference,
  updateMood,
  createChatSession,
  sendMessage
} = useUser();
```

## 🎨 Style Design

### Design System
- **Primary Color**: #667eea (Purple-blue)
- **Secondary Color**: #764ba2 (Purple)
- **Success Color**: #10b981 (Green)
- **Warning Color**: #f59e0b (Orange)
- **Error Color**: #ef4444 (Red)

### Component Styling
Use `styled-components` for style management:

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

## 📱 Responsive Design

### Breakpoint Settings
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px  
- **Desktop**: > 1024px

### Adaptive Layout
```css
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
```

## 🔍 Error Handling

### API Error Handling
```javascript
try {
  const result = await apiService.someMethod();
  toast.success('Operation successful');
} catch (error) {
  console.error('Operation failed:', error);
  toast.error('Operation failed, please try again');
}
```

### Loading States
```javascript
const [loading, setLoading] = useState(false);

// Show loading component
if (loading) {
  return <LoadingSpinner text="Loading..." />;
}
```

## 🧪 Testing

### Feature Testing Checklist
- [ ] User login/registration flow
- [ ] Profile editing
- [ ] Preference settings management
- [ ] AI chat functionality
- [ ] Recommendation history viewing
- [ ] Feedback submission functionality

### Test Commands
```bash
npm test
```

## 🚀 Deployment

### Build Production Version
```bash
npm run build
```

### Deploy to Static Hosting
Built files are in the `build/` directory and can be deployed to:
- Vercel
- Netlify
- GitHub Pages
- AWS S3

## 🔧 Development Tools

### Recommended VS Code Extensions
- ES7+ React/Redux/React-Native snippets
- Prettier - Code formatter
- Auto Rename Tag
- Bracket Pair Colorizer

### Debugging Tools
- React Developer Tools
- Redux DevTools (if using Redux)

## 📝 Usage Instructions

### 1. First Time Use
1. Visit the application homepage
2. Click login/register
3. Login with email or social account
4. Complete profile and preference settings

### 2. Daily Use
1. View overview information on dashboard
2. Enter AI chat interface to start conversation
3. Get recommendations based on mood and preferences
4. View and rate recommendations in recommendation history

### 3. Personalization Settings
1. Set preferences on profile page
2. Regularly update mood state
3. Improve recommendation quality through feedback

## 🐛 Common Issues

### Q: Blank page after login?
A: Check if backend service is running normally, confirm API address configuration is correct

### Q: Unable to get recommendations?
A: Confirm user preferences are set, check network connection and backend service status

### Q: Styling display issues?
A: Clear browser cache, confirm CSS files are loading normally

## 📞 Technical Support

If you encounter problems, please check:
1. Backend service is running normally
2. Environment variable configuration is correct
3. Network connection is normal
4. Browser console has no error messages

---

*This React frontend application is perfectly integrated with the backend Clerk user management system, providing a complete user experience and feature coverage.*
