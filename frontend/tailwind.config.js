/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        netflix: {
          black: "#141414",
          red: "#E50914",
          green: "#46d369",
          darkGray: "#181818",
        }
      },
      backgroundImage: {
        'gradient-to-b-netflix': 'linear-gradient(to bottom, rgba(20,20,20,0) 0%, rgba(20,20,20,.15) 15%, rgba(20,20,20,.35) 29%, rgba(20,20,20,.58) 44%, #141414 68%, #141414 100%)',
      }
    },
  },
  plugins: [],
}
