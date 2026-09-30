module.exports = {
  darkMode: "class",
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  safelist: [
    "bg-amber-400",
    "bg-amber-600",
    "bg-gray-300",
    "h-10",
    "h-14",
    "h-20",
    "text-base",
    "text-xl",
    "text-green-600",
    "text-blue-600",
    "text-yellow-600",
    "text-red-500",
    "w-12",
    "w-16",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
        sena: {
          DEFAULT: "#39A900",
          light: "#4ADE80",
          dark: "#2d8a00",
          50: "#f0fff0",
          100: "#dcfce7",
        },
        accent: {
          DEFAULT: "#FFC107",
          400: "#FBBF24",
          500: "#FFC107",
          600: "#D97706",
        },
        dark: {
          bg: "#0B0F14",
          card: "#111827",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
