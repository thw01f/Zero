/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ft: {
          bg:      '#0a0e1a',
          surface: '#0f1526',
          card:    '#141d30',
          hover:   '#1a2540',
          border:  '#1e2d47',
          'border-light': '#263553',
          accent:  '#f26d21',
          'accent-dim': '#c45518',
          'accent-glow': 'rgba(242,109,33,0.15)',
          blue:    '#4a9ff5',
          cyan:    '#26c6da',
          green:   '#3ecf8e',
          yellow:  '#f5a623',
          red:     '#f25555',
          'red-dim': '#c43a3a',
          purple:  '#a78bfa',
          'text':        '#dde3ef',
          'text-dim':    '#8a96b0',
          'text-muted':  '#4a5568',
          'text-accent': '#f26d21',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Consolas', '"Courier New"', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
      },
      boxShadow: {
        'ft': '0 2px 8px rgba(0,0,0,0.4)',
        'ft-lg': '0 4px 24px rgba(0,0,0,0.5)',
        'accent': '0 0 12px rgba(242,109,33,0.3)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan-line': 'scanline 2s linear infinite',
      },
    },
  },
  plugins: [],
}
