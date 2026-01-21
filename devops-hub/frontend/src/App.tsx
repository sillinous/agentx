import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Layout, LoadingScreen, ToastProvider, CommandPalette, useCommandPalette } from './components/ui';
import {
  Dashboard,
  Agents,
  AgentDetail,
  Workflows,
  WorkflowDetail,
  WorkflowBuilder,
  Evaluations,
  Health,
  Handbook,
  Portfolio,
  HumanActions,
  Integrations,
  Login,
  Settings,
  NotFound,
  ServerError,
} from './pages';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

// Error Boundary component
interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <ServerError
          error={this.state.error || undefined}
          resetErrorBoundary={() => this.setState({ hasError: false, error: null })}
        />
      );
    }

    return this.props.children;
  }
}

// Protected route wrapper
function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

// Command Palette wrapper (needs to be inside BrowserRouter for navigation)
function CommandPaletteWrapper() {
  const { isOpen, close } = useCommandPalette();
  return <CommandPalette isOpen={isOpen} onClose={close} />;
}

// App routes component (needs to be inside AuthProvider)
function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <>
      <CommandPaletteWrapper />
      <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <Login />}
      />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/agents"
        element={
          <ProtectedRoute>
            <Layout>
              <Agents />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/agents/:agentId"
        element={
          <ProtectedRoute>
            <Layout>
              <AgentDetail />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows"
        element={
          <ProtectedRoute>
            <Layout>
              <Workflows />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows/:workflowId"
        element={
          <ProtectedRoute>
            <Layout>
              <WorkflowDetail />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/evaluations"
        element={
          <ProtectedRoute>
            <Layout>
              <Evaluations />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/health"
        element={
          <ProtectedRoute>
            <Layout>
              <Health />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/handbook"
        element={
          <ProtectedRoute>
            <Layout>
              <Handbook />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/portfolio"
        element={
          <ProtectedRoute>
            <Layout>
              <Portfolio />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/human-actions"
        element={
          <ProtectedRoute>
            <Layout>
              <HumanActions />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Layout>
              <Settings />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/integrations"
        element={
          <ProtectedRoute>
            <Layout>
              <Integrations />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows/builder"
        element={
          <ProtectedRoute>
            <Layout>
              <WorkflowBuilder />
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* Error routes */}
      <Route path="/error" element={<ServerError />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
    </>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <ToastProvider>
            <AuthProvider>
              <BrowserRouter>
                <AppRoutes />
              </BrowserRouter>
            </AuthProvider>
          </ToastProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
