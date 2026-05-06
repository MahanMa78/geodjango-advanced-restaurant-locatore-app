
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Syne', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        brand: {
          DEFAULT: '#E8420A',
          light: '#FF6B35',
          soft: '#FFF0EB',
        },
        surface: '#FAFAF8',
        ink: {
          DEFAULT: '#1A1A18',
          muted: '#6B6860',
          faint: '#9E9B94',
        },
        edge: {
          DEFAULT: '#ECEAE4',
          dark: '#D4D0C8',
        },
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.04)',
        panel: '0 4px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04)',
        lift: '0 12px 32px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.05)',
        float: '-4px 0 20px rgba(0,0,0,0.08)',
      },
      borderRadius: {
        xl2: '20px',
      },
      animation: {
        'fade-up': 'fadeUp 0.22s ease both',
        'slide-up': 'slideUp 0.3s cubic-bezier(0.32,0.72,0,1) both',
        'pulse-dot': 'pulseDot 1.4s ease infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        pulseDot: {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.4' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}