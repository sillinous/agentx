'use client';

import Link from 'next/link';
import UserMenu from './UserMenu';

export default function Header() {
    return (
        <header className="bg-white shadow-sm py-4 px-6">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
                <Link href="/" className="text-2xl font-bold text-gray-800 hover:text-gray-600 transition-colors">
                    Unified Media Asset Manager
                </Link>
                <UserMenu />
            </div>
        </header>
    );
}
