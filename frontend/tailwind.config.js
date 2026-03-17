/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        forge: {
          bg: '#080c14',
          surface: '#0d1321',
          border: '#1a2540',
          accent: '#00d4ff',
          green: '#00ff88',
          red: '#ff4444',
          orange: '#ff8800',
          yellow: '#ffd700',
          muted: '#4a5568',
          text: '#e2e8f0',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          from: { boxShadow: '0 0 5px #00d4ff33' },
          to: { boxShadow: '0 0 20px #00d4ff66, 0 0 40px #00d4ff22' },
        }
      }
    },
  },
  plugins: [],
}
