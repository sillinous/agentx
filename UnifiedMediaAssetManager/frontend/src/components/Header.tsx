'use client';

import Link from 'next/link';
import UserMenu from './UserMenu';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const navLinks = [
  { href: '/', label: 'Dashboard' },
  { href: '/universes', label: 'Universes' },
  { href: '/gallery', label: 'Media Gallery' },
  { href: '/images', label: 'Image Studio' },
  { href: '/audio', label: 'Audio Studio' },
  { href: '/hitl', label: 'Agent Requests' },
  { href: '/dashboard/analytics', label: 'Analytics' },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-2xl font-bold text-gray-800 hover:text-gray-600 transition-colors">
              Aetheria Studio
            </Link>
            <nav className="hidden md:flex space-x-6">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    'text-sm font-medium transition-colors',
                    pathname === link.href
                      ? 'text-blue-600'
                      : 'text-gray-500 hover:text-gray-900'
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center">
            <UserMenu />
          </div>
        </div>
      </div>
    </header>
  );
}
