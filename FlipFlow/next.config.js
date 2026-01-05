/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: [
      'flippa.com',
      'www.flippa.com',
      'd1csarkz8obe9u.cloudfront.net', // Flippa CDN
    ],
  },
  experimental: {
    serverActions: {
      allowedOrigins: ['localhost:3000'],
    },
  },
  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_APP_NAME: 'FlipFlow',
    NEXT_PUBLIC_APP_DESCRIPTION: 'AI-Powered Digital Business Intelligence',
  },
}

module.exports = nextConfig
