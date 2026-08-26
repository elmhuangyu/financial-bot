import daisyui from "daisyui";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [daisyui],
  daisyui: {
    themes: [
      {
        darkFinancial: {
          primary: "#22c55e",
          secondary: "#0ea5e9",
          accent: "#f59e0b",
          neutral: "#1e293b",
          "base-100": "#020617",
          "base-200": "#0f172a",
          "base-300": "#1e293b",
          info: "#38bdf8",
          success: "#10b981",
          warning: "#f59e0b",
          error: "#f43f5e",
        },
      },
      "dark",
      "night",
      "dim",
      "nord",
    ],
    defaultTheme: "darkFinancial",
  },
};
