import Aura from "@primeuix/themes/aura"
import PrimeUI from "tailwindcss-primeui"
import { definePreset } from "@primeuix/themes"

export default defineNuxtConfig({
  compatibilityDate: "2024-04-03",
  devtools: { enabled: true },
  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE,
      appBaseurl: process.env.APP_BASEURL,
    },
  },
  app: {
    baseURL: process.env.APP_BASEURL,
    head: {
      link: [
        { rel: "shortcut icon", href: process.env.APP_BASEURL + "favicon.ico" },
        {
          id: "theme-link",
          rel: "stylesheet",
        },
      ],
    },
  },
  modules: [
    "@pinia/nuxt",
    "@nuxt/eslint",
    "@nuxtjs/tailwindcss",
    "@primevue/nuxt-module",
    "@nuxtjs/i18n",
  ],

  primevue: {
    options: {
      theme: {
        preset: Aura,
        options: {
          prefix: "p",
        },
      },
      ripple: true,
    },
    autoImport: true,
  },
  tailwindcss: {
    config: {
      plugins: [PrimeUI],
      // darkMode: ["class", ".p-dark"],
    },
  },

  css: ["primeicons/primeicons.css", "~/assets/css/global.css"],
  
  nitro: {
    devProxy: {
      "/api": {
        target: "http://localhost:5008/api",
        changeOrigin: true
      }
    }
  }
})
