import React from 'react';
import { ClerkProvider, SignedIn, SignedOut } from '@clerk/clerk-react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import styled from 'styled-components';

// Components
import Header from './components/Header';
import LandingPage from './components/LandingPage';
import Dashboard from './components/Dashboard';
import Profile from './components/Profile';
import ChatInterface from './components/ChatInterface';
import Recommendations from './components/Recommendations';
import { UserProvider } from './contexts/UserContext';

// Styled Components
const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
`;

const MainContent = styled.main`
  min-height: calc(100vh - 80px);
  padding: 20px;
`;

// Clerk configuration
const clerkPubKey = process.env.REACT_APP_CLERK_PUBLISHABLE_KEY || 'pk_test_cHJlY2lzZS1jb3VnYXItNTIuY2xlcmsuYWNjb3VudHMuZGV2JA';

function App() {
  return (
    <ClerkProvider publishableKey={clerkPubKey}>
      <Router>
        <AppContainer>
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
          
          <SignedOut>
            <LandingPage />
          </SignedOut>
          
          <SignedIn>
            <UserProvider>
              <Header />
              <MainContent>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/chat" element={<ChatInterface />} />
                  <Route path="/recommendations" element={<Recommendations />} />
                </Routes>
              </MainContent>
            </UserProvider>
          </SignedIn>
        </AppContainer>
      </Router>
    </ClerkProvider>
  );
}

export default App;
