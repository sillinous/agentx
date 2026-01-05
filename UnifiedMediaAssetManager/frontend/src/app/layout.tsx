import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Unified Media Asset Manager",
  description: "A platform for managing and generating media.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning={true}>
      <body suppressHydrationWarning={true} className="bg-gray-100 text-gray-900">
        <header className="bg-white shadow-sm py-4 px-6">
          <div className="max-w-7xl mx-auto">
            <h1 className="text-2xl font-bold text-gray-800">Unified Media Asset Manager</h1>
          </div>
        </header>
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {children}
        </main>
      </body>
    </html>
  );
}
