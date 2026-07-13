/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0E1019",
          900: "#12141F",
          800: "#1B1E2E",
          700: "#262A3D",
          600: "#343956",
        },
        gold: {
          400: "#D9BA72",
          500: "#C9A24B",
          600: "#AD873A",
        },
        sage: "#7FA37A",
        rust: "#B4694A",
        parchment: "#EDEAE2",
        mute: "#9497AA",
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        sans: ["'Inter'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
    },
  },
  plugins: [],
}

