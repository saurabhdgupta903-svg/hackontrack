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
        background: "#FAFAF7",
        foreground: "#1A1A1A",
        accent: {
          DEFAULT: "#1B4D3E", // Deep forest green accent
          hover: "#143A2F",
          light: "#E8F0EC",
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
        DEFAULT: "6px",
        md: "8px",
      },
    },
  },
  plugins: [],
};
