import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: "#0A0E14", surface: "#12161F", elevated: "#181D28" },
        border: { DEFAULT: "#1F2733" },
        text: { primary: "#E6EAF0", muted: "#8993A8", faint: "#5A6479" },
        accent: {
          gain: "#22D3B8",
          loss: "#F0554A",
          signal: "#F0B429",
        },
        keyframes: {
        scroll: { "0%": { transform: "translateX(0)" }, "100%": { transform: "translateX(-50%)" } },
      }
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "monospace"],
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;