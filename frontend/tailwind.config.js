/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Option C — Clean + Illustrative (Friendly) Design Tokens
        brand: {
          50: '#F0F7F4',
          100: '#E0EFE9',
          200: '#C1E0D4',
          300: '#8CC5B0',
          400: '#45A586',
          500: '#15966F', // Emerald
          600: '#08765B', // Primary green
          700: '#075443', // Deep forest
          800: '#053F32',
          900: '#042D24',
          950: '#021C16',
        },
        forest: {
          DEFAULT: '#075443',
          deep: '#053F32',
          dark: '#042D24',
        },
        emerald: {
          DEFAULT: '#15966F',
        },
        warmwhite: '#FCFBF7',
        purewhite: '#FFFFFF',
        softbeige: {
          DEFAULT: '#F4EDE2',
          light: '#FAF5ED',
          dark: '#EADBCA',
        },
        charcoal: {
          DEFAULT: '#18231F',
          muted: '#64716C',
          light: '#8C9B95',
        },
        mutedgrey: '#64716C',
        softorange: {
          DEFAULT: '#D99143',
          50: '#FDF8F2',
          100: '#F9EEDD',
          200: '#F3DBBB',
          300: '#ECC798',
          400: '#E3AB6E',
          500: '#D99143',
          600: '#C47D32',
          700: '#A46325',
        },
        bordergrey: '#E5EAE6',
        tealbrand: {
          50: '#F0F7F4',
          100: '#E0EFE9',
          500: '#15966F',
          600: '#08765B',
          700: '#075443',
        },
        amberbrand: {
          50: '#FDF8F2',
          100: '#F9EEDD',
          400: '#E3AB6E',
          500: '#D99143',
          600: '#C47D32',
          700: '#A46325',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          warm: '#FCFBF7',
          beige: '#F4EDE2',
          muted: '#FAF8F5',
          subtle: '#F4EDE2',
          border: '#E5EAE6',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        'option-c': '0 2px 10px rgba(7, 84, 67, 0.05), 0 1px 3px rgba(24, 35, 31, 0.05)',
        'option-c-md': '0 4px 20px rgba(7, 84, 67, 0.08), 0 2px 6px rgba(24, 35, 31, 0.06)',
        'option-c-lg': '0 10px 30px rgba(7, 84, 67, 0.12), 0 4px 10px rgba(24, 35, 31, 0.08)',
      },
    },
  },
  plugins: [],
}
