/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: "#0B0D0F",
          900: "#12151A",
          800: "#1A1F26",
          700: "#242B34",
          600: "#333C48",
          500: "#4A5563",
        },
        signal: {
          400: "#4DD8C7",
          500: "#2CC2AE",
          600: "#1FA592",
        },
        alert: {
          500: "#E0554F",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "system-ui", "sans-serif"],
        body: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
