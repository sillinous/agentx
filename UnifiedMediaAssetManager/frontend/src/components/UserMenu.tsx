'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export default function UserMenu() {
    const { user, isAuthenticated, isLoading, logout, hasRole } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    // Close menu when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    if (isLoading) {
        return (
            <div className="h-8 w-8 rounded-full bg-gray-200 animate-pulse"></div>
        );
    }

    if (!isAuthenticated) {
        return (
            <div className="flex items-center gap-3">
                <Link
                    href="/login"
                    className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
                >
                    Sign in
                </Link>
                <Link
                    href="/register"
                    className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 transition-colors"
                >
                    Register
                </Link>
            </div>
        );
    }

    const initials = (user?.display_name || user?.username || 'U')
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);

    return (
        <div className="relative" ref={menuRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 focus:outline-none"
            >
                <div className="h-8 w-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-medium">
                    {initials}
                </div>
                <span className="text-sm text-gray-700 hidden sm:block">
                    {user?.display_name || user?.username}
                </span>
                <svg
                    className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50">
                    <div className="py-1">
                        <div className="px-4 py-2 border-b border-gray-100">
                            <p className="text-sm font-medium text-gray-900">{user?.display_name || user?.username}</p>
                            <p className="text-xs text-gray-500">{user?.email || 'No email'}</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                                {user?.roles.map(role => (
                                    <span
                                        key={role}
                                        className="inline-block px-1.5 py-0.5 text-xs rounded bg-gray-100 text-gray-600"
                                    >
                                        {role}
                                    </span>
                                ))}
                            </div>
                            {user?.is_test_user && (
                                <span className="inline-block mt-1 px-1.5 py-0.5 text-xs rounded bg-yellow-100 text-yellow-800">
                                    Test User
                                </span>
                            )}
                        </div>

                        <Link
                            href="/"
                            onClick={() => setIsOpen(false)}
                            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                            Home
                        </Link>

                        {hasRole('admin') && (
                            <div className="border-t border-gray-100">
                                <span className="block px-4 py-1 text-xs text-gray-400 uppercase">Admin</span>
                                <Link
                                    href="/admin"
                                    onClick={() => setIsOpen(false)}
                                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                >
                                    Admin Panel
                                </Link>
                            </div>
                        )}

                        <div className="border-t border-gray-100">
                            <button
                                onClick={() => {
                                    logout();
                                    setIsOpen(false);
                                }}
                                className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                            >
                                Sign out
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
