import type { Config } from "tailwindcss";

const config: Config = {
  // This is the key part for your toggle to work
  darkMode: "class",

  content: [
    // These paths look inside your 'src' folder shown in the image
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'), // Ensure you have this installed since you use 'prose'
  ],
};
export default config;