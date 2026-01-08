'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { AUTH_ERROR_EVENT } from '@/services/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const TOKEN_KEY = 'UMAM_TOKEN';

export interface User {
    id: string;
    username: string;
    email: string | null;
    display_name: string | null;
    roles: string[];
    is_test_user: boolean;
}

interface AuthState {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
    login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
    register: (username: string, password: string, displayName?: string, email?: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => void;
    hasRole: (role: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const [state, setState] = useState<AuthState>({
        user: null,
        token: null,
        isLoading: true,
        isAuthenticated: false,
    });

    // Load token from localStorage on mount
    useEffect(() => {
        const storedToken = localStorage.getItem(TOKEN_KEY);
        if (storedToken) {
            // Validate token by fetching current user
            fetchCurrentUser(storedToken);
        } else {
            setState(prev => ({ ...prev, isLoading: false }));
        }
    }, []);

    // Listen for auth errors (401) from API calls
    useEffect(() => {
        const handleAuthError = () => {
            // Clear auth state and redirect to login
            localStorage.removeItem(TOKEN_KEY);
            setState({ user: null, token: null, isLoading: false, isAuthenticated: false });
            if (pathname !== '/login' && pathname !== '/register') {
                router.push('/login');
            }
        };
        window.addEventListener(AUTH_ERROR_EVENT, handleAuthError);
        return () => window.removeEventListener(AUTH_ERROR_EVENT, handleAuthError);
    }, [router, pathname]);

    const fetchCurrentUser = async (token: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (response.ok) {
                const user = await response.json();
                setState({
                    user,
                    token,
                    isLoading: false,
                    isAuthenticated: true,
                });
            } else {
                // Token invalid, clear it
                localStorage.removeItem(TOKEN_KEY);
                setState({ user: null, token: null, isLoading: false, isAuthenticated: false });
            }
        } catch {
            localStorage.removeItem(TOKEN_KEY);
            setState({ user: null, token: null, isLoading: false, isAuthenticated: false });
        }
    };

    const login = useCallback(async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem(TOKEN_KEY, data.access_token);
                setState({
                    user: data.user,
                    token: data.access_token,
                    isLoading: false,
                    isAuthenticated: true,
                });
                return { success: true };
            } else {
                const errorData = await response.json().catch(() => ({}));
                return { success: false, error: errorData.detail || 'Login failed' };
            }
        } catch (err) {
            return { success: false, error: 'Network error. Please try again.' };
        }
    }, []);

    const register = useCallback(async (
        username: string,
        password: string,
        displayName?: string,
        email?: string
    ): Promise<{ success: boolean; error?: string }> => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username,
                    password,
                    display_name: displayName || username,
                    email: email || null,
                }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem(TOKEN_KEY, data.access_token);
                setState({
                    user: data.user,
                    token: data.access_token,
                    isLoading: false,
                    isAuthenticated: true,
                });
                return { success: true };
            } else {
                const errorData = await response.json().catch(() => ({}));
                return { success: false, error: errorData.detail || 'Registration failed' };
            }
        } catch (err) {
            return { success: false, error: 'Network error. Please try again.' };
        }
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem(TOKEN_KEY);
        setState({
            user: null,
            token: null,
            isLoading: false,
            isAuthenticated: false,
        });
    }, []);

    const hasRole = useCallback((role: string): boolean => {
        return state.user?.roles.includes(role) ?? false;
    }, [state.user]);

    return (
        <AuthContext.Provider value={{ ...state, login, register, logout, hasRole }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
