/** @type {import('tailwindcss').Config} */
const _ = require('lodash');
const customConfig = require('./tailwind.config.custom');
const baseConfig = {
  
  content: [
    "./web/templates/*.html",
    "./web/templates/**/*.html",
    "./boilersaas/src/boilerssas/templates/*.html",
    "./boilersaas/src/boilersaas/templates/**/*.html"
  ],

  plugins: [require("@tailwindcss/typography"), require("daisyui")], // order matters
  daisyui: {
       darkTheme: "dark", // name of one of the included themes for dark mode
    base: true, // applies background color and foreground color for root element by default
    styled: true, // include daisyUI colors and design decisions for all components
    utils: true, // adds responsive and modifier utility classes
    prefix: "", // prefix for daisyUI classnames (components, modifiers and responsive class names. Not colors)
    logs: true, // Shows info about daisyUI version and used config in the console when building your CSS
    themeRoot: ":root", // The element that receives theme color CSS variables
  },
}

module.exports = _.merge(baseConfig, customConfig);