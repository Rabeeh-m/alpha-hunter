import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "var(--bg-default, #F8FAFC)",
          surface: "var(--bg-surface, #FFFFFF)",
          section: "var(--bg-section, #F5F7FA)",
          elevated: "var(--bg-elevated, #F1F5F9)",
          subtle: "var(--bg-subtle, #FAFBFC)",
          hover: "var(--bg-hover, #F9FBFD)",
        },
        border: {
          DEFAULT: "var(--border-default, #E5E7EB)",
          light: "var(--border-light, #EEF2F7)",
        },
        text: {
          primary: "var(--text-primary, #111827)",
          secondary: "var(--text-secondary, #4B5563)",
          muted: "var(--text-muted, #9CA3AF)",
          faint: "var(--text-faint, #D1D5DB)",
        },
        brand: {
          primary: "var(--brand-primary, #3861FB)",
          "primary-hover": "var(--brand-primary-hover, #2954F5)",
          "primary-light": "var(--brand-primary-light, #EEF3FF)",
          success: "var(--brand-success, #16C784)",
          "success-light": "var(--brand-success-light, #E9FFF4)",
          danger: "var(--brand-danger, #EA3943)",
          "danger-light": "var(--brand-danger-light, #FFF1F3)",
          warning: "var(--brand-warning, #F59E0B)",
          "warning-light": "var(--brand-warning-light, #FFF7E6)",
          info: "var(--brand-info, #0EA5E9)",
          "info-light": "var(--brand-info-light, #F0F9FF)",
        },
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 2px 10px rgba(0,0,0,.05)",
        elevated: "0 10px 35px rgba(15,23,42,.08)",
        modal: "0 20px 50px rgba(15,23,42,.12)",
        glass: "0 1px 3px 0 rgba(0,0,0,.04)",
        "card-hover": "0 4px 20px rgba(0,0,0,.08)",
      },
      keyframes: {
        scroll: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in": {
          "0%": { opacity: "0", transform: "translateX(-8px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-out",
        "slide-in": "slide-in 0.2s ease-out",
      },
    },
  },
  plugins: [],
} satisfies Config;
