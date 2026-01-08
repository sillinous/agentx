'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export default function LoginPage() {
    const router = useRouter();
    const { login, isAuthenticated, isLoading } = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);

    // Redirect if already authenticated
    if (isAuthenticated && !isLoading) {
        router.push('/');
        return null;
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSubmitting(true);

        const result = await login(username, password);

        if (result.success) {
            router.push('/');
        } else {
            setError(result.error || 'Login failed');
        }
        setSubmitting(false);
    };

    const fillTestUser = (user: string, pass: string) => {
        setUsername(user);
        setPassword(pass);
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                        Sign in to your account
                    </h2>
                    <p className="mt-2 text-center text-sm text-gray-600">
                        Or{' '}
                        <Link href="/register" className="font-medium text-blue-600 hover:text-blue-500">
                            create a new account
                        </Link>
                    </p>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
                            {error}
                        </div>
                    )}

                    <div className="rounded-md shadow-sm -space-y-px">
                        <div>
                            <label htmlFor="username" className="sr-only">Username</label>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                                placeholder="Username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="sr-only">Password</label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            disabled={submitting}
                            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {submitting ? 'Signing in...' : 'Sign in'}
                        </button>
                    </div>
                </form>

                {/* Test Users Section */}
                <div className="mt-6 border-t border-gray-200 pt-6">
                    <p className="text-sm text-gray-500 text-center mb-3">Quick login (test users):</p>
                    <div className="grid grid-cols-2 gap-2">
                        <button
                            type="button"
                            onClick={() => fillTestUser('test_admin', 'TestAdmin123!')}
                            className="px-3 py-2 text-xs border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                        >
                            Admin
                        </button>
                        <button
                            type="button"
                            onClick={() => fillTestUser('test_editor', 'TestEditor123!')}
                            className="px-3 py-2 text-xs border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                        >
                            Editor
                        </button>
                        <button
                            type="button"
                            onClick={() => fillTestUser('test_viewer', 'TestViewer123!')}
                            className="px-3 py-2 text-xs border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                        >
                            Viewer
                        </button>
                        <button
                            type="button"
                            onClick={() => fillTestUser('test_creator', 'TestCreator123!')}
                            className="px-3 py-2 text-xs border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                        >
                            Creator
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
