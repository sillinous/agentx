/* eslint-disable @typescript-eslint/no-require-imports */
const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  outputFileTracingRoot: path.join(__dirname, '../../'),
};

module.exports = nextConfig;
