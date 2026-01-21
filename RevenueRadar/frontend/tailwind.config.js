/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        tier1: '#22c55e',
        tier2: '#eab308',
        tier3: '#6b7280',
      },
    },
  },
  plugins: [],
}
