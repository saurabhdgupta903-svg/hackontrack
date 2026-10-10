/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--wa-bg)",
        foreground: "var(--wa-text)",
        "wa-bg": "#efeae2",
        "wa-bubble": "#d9fdd3",
        "wa-bubble-dark": "#c5ecbd",
        "wa-accent": "#00a884",
        "wa-accent-hover": "#008f6f",
        "wa-text": "#111b21",
        "wa-text-muted": "#8696a0",
        "wa-bar": "#f0f2f5",
        "wa-border": "#d1d7db",
        accent: {
          DEFAULT: "#00a884",
          hover: "#008f6f",
          light: "#d9fdd3",
        },
        verdict: {
          verified: "#15803D",
          "verified-bg": "#F0FDF4",
          "verified-border": "#BBF7D0",

          false: "#B91C1C",
          "false-bg": "#FEF2F2",
          "false-border": "#FECACA",

          outdated: "#C2410C",
          "outdated-bg": "#FFF7ED",
          "outdated-border": "#FFEDD5",

          partly: "#B45309",
          "partly-bg": "#FFFBEB",
          "partly-border": "#FDE68A",

          unconfirmed: "#475569",
          "unconfirmed-bg": "#F8FAFC",
          "unconfirmed-border": "#E2E8F0",
        },
      },
      borderRadius: {
        DEFAULT: "12px",
        md: "12px",
        "wa-bubble": "4px 12px 12px 12px",
        "wa-pill": "9999px",
      },
      boxShadow: {
        "wa-bubble": "0 1px 0.5px rgba(0, 0, 0, 0.13)",
      },
    },
  },
  plugins: [],
};
