/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "'Noto Sans Khmer'", "system-ui", "sans-serif"],
        khmer: ["'Noto Sans Khmer'", "Battambang", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#17243a",
        muted: "#7b879b",
        brand: "#5c62e8",
        canvas: "#f5f7fb",
      },
      boxShadow: {
        card: "0 6px 24px rgba(23, 36, 58, 0.055)",
      },
    },
  },
  plugins: [],
};
