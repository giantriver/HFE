module.exports = {
    darkMode: "class",
    content: [
        './components/**/*.{vue,js,jsx,tsx}',
        './layouts/**/*.vue',
        './pages/**/*.vue',
        './plugins/**/*.{js,ts}',
        './app.vue',
        './nuxt.config.{js,ts}'
    ],
    theme: {
        extend: {},
    },
    variants: {
        extend: {},
    },
    plugins: [
        require('tailwindcss-primeui')
    ],
}
