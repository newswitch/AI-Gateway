/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1677ff',
        success: '#52c41a',
        danger: '#ff4d4f',
        warning: '#FF7D00',
        secondary: '#0FC6C2',
        dark: '#1D2129',
        'dark-2': '#4E5969',
        'light-1': '#F2F3F5',
        'light-2': '#E5E6EB',
        'light-3': '#8c8c8c'
      }
    }
  },
  safelist: [
    'bg-primary/10', 'text-primary', 'text-success', 'text-danger',
    'policy-badge', 'token-badge'
  ],
  plugins: []
}


