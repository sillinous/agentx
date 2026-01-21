import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'RevenueRadar - Monetization Dashboard',
  description: 'Monitor and accelerate monetization across your portfolio',
};

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
    >
      {children}
    </Link>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          {/* Header */}
          <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between h-16">
                <div className="flex items-center gap-8">
                  <Link href="/" className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-sm">RR</span>
                    </div>
                    <span className="font-semibold text-gray-900">RevenueRadar</span>
                  </Link>

                  <nav className="flex items-center gap-1">
                    <NavLink href="/">Dashboard</NavLink>
                    <NavLink href="/projects">Projects</NavLink>
                    <NavLink href="/pipeline">Pipeline</NavLink>
                    <NavLink href="/quickwins">Quick Wins</NavLink>
                  </nav>
                </div>

                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-500">
                    Portfolio Monetization Hub
                  </span>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
