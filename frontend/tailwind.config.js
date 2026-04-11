/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'krystal-dark': '#0a0e1a',
        'krystal-darker': '#050810',
        'krystal-blue': '#1e40af',
        'krystal-cyan': '#06b6d4',
        'krystal-purple': '#7c3aed',
      },
    },
  },
  plugins: [],
}
