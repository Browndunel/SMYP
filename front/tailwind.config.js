/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Mapping complet de tes variables CSS
                border: "oklch(var(--border) / <alpha-value>)",
                input: "oklch(var(--input) / <alpha-value>)",
                ring: "oklch(var(--ring) / <alpha-value>)",
                background: "oklch(var(--background) / <alpha-value>)",
                foreground: "oklch(var(--foreground) / <alpha-value>)",
                primary: {
                    DEFAULT: "oklch(var(--primary) / <alpha-value>)",
                    foreground: "oklch(var(--primary-foreground) / <alpha-value>)",
                },
                secondary: {
                    DEFAULT: "oklch(var(--secondary) / <alpha-value>)",
                    foreground: "oklch(var(--secondary-foreground) / <alpha-value>)",
                },
                destructive: {
                    DEFAULT: "oklch(var(--destructive) / <alpha-value>)",
                    foreground: "oklch(var(--destructive-foreground) / <alpha-value>)",
                },
                muted: {
                    DEFAULT: "oklch(var(--muted) / <alpha-value>)",
                    foreground: "oklch(var(--muted-foreground) / <alpha-value>)",
                },
                accent: {
                    DEFAULT: "oklch(var(--accent) / <alpha-value>)",
                    foreground: "oklch(var(--accent-foreground) / <alpha-value>)",
                },
                popover: {
                    DEFAULT: "oklch(var(--popover) / <alpha-value>)",
                    foreground: "oklch(var(--popover-foreground) / <alpha-value>)",
                },
                card: {
                    DEFAULT: "oklch(var(--card) / <alpha-value>)",
                    foreground: "oklch(var(--card-foreground) / <alpha-value>)",
                },
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
            },
            animation: {
                'spin-slow': 'spin 3s linear infinite',
                'marquee': 'marquee 8s linear infinite', // Ajout de l'animation pour ton titre
            },
            keyframes: {
                marquee: {
                    '0%': { transform: 'translateX(-100%)' },
                    '100%': { transform: 'translateX(100%)' },
                },
            },
        },
    },
    plugins: [],
}