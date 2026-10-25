import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        "bg-base": "var(--bg-base)",
        "bg-surface": "var(--bg-surface)",
        "bg-sunken": "var(--bg-sunken)",
        "ink-primary": "var(--ink-primary)",
        "ink-ghost": "var(--ink-ghost)",
        "accent-primary": "var(--accent-primary)",
        "accent-cite": "var(--accent-cite)",
        "accent-hot": "var(--accent-hot)",
        "status-retrieve": "var(--status-retrieve)",
        "status-rerank": "var(--status-rerank)",
        "status-twohop": "var(--status-twohop)",
        "status-cache": "var(--status-cache)",
        "gray-warm": "var(--gray-warm)",
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "sans-serif"],
        display: ["var(--font-display)", "Bricolage Grotesque", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
        handwriting: ["var(--font-handwriting)", "Caveat", "cursive"],
        editorial: ["Georgia", "Hiragino Mincho ProN", "serif"],
      },
      borderRadius: {
        interactive: "10px",
        input: "4px",
        chrome: "0px",
        lg: "10px",
        md: "6px",
        sm: "4px",
      },
      animation: {
        "fade-in": "fadeIn 200ms cubic-bezier(0.3, 0.7, 0.3, 1)",
        "slide-up": "slideUp 320ms cubic-bezier(0.22, 1, 0.36, 1)",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
