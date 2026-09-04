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
        gov: {
          saffron: "#E05A10",
          "saffron-dark": "#B84305",
          "saffron-light": "#FFF3EC",
          yellow: "#E89B1C",
          "yellow-dark": "#C27806",
          "yellow-light": "#FFFBEB",
          navy: "#1E293B",
          charcoal: "#1F2937",
          gray: "#F8F9FA",
          "gray-dark": "#4B5563",
          border: "#D1D5DB",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        gov: "0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px -1px rgba(0, 0, 0, 0.08)",
        "gov-md": "0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.08)",
      },
    },
  },
  plugins: [],
};
