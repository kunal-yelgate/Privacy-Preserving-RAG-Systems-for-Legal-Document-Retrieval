/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        legal: {
          900: "#0b1329",
          800: "#131f42",
          700: "#1c2e63",
          600: "#2a438c",
          500: "#3d62c7",
          400: "#6587e6",
          100: "#e9effd",
          50: "#f4f7fe",
        },
      },
    },
  },
  plugins: [],
};
