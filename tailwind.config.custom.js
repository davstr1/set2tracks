const plugin = require('tailwindcss/plugin');
const customConfig = {
  daisyui: {
    themes: [
      {
        set2tracks: {

          "primary": "oklch(65.69% 0.196 275.75)",
          "primary-content": "#1D232A", // 2a323c
          "secondary": "oklch(74.8% 0.26 342.55)",
          "accent": "oklch(74.51% 0.167 183.61)",
          "neutral": "#2a323c",
          "neutral-content": "#A6ADBB",
          "base-100": "#1d232a",
          "base-200": "#191e24",
          "base-300": "#15191e",
          "base-content": "#A6ADBB",
          // var(--fallback-b1,oklch(var(--b1)/1))
        },
      },
    ],
  },
  plugins: [
    plugin(function({ addComponents }) {
      addComponents({
        'input[type=text]': {
          '@apply appearance-none outline-none rounded-lg bg-transparent w-full ring-1 ring-current focus:ring-primary focus:ring-1   p-2 mb-2 mt-2': {},
        },
        'input[type=password]': {
          '@apply appearance-none outline-none rounded-lg bg-transparent w-full ring-1 ring-current focus:ring-primary focus:ring-1   p-2 mb-2 mt-2': {},
        },
        '.form-wrapper': {
          '@apply sm:border sm:border-current w-full max-w-sm rounded-lg p-4 content-center': {},
        },
        '.track.active': {
          '@apply ring-2 ring-primary': {},
        },
        '.track.active .bar-vertical': {
          '@apply bg-primary': {},
        },
        '.hypotetic': {
          '@apply opacity-40': {}, // border  border-dashed border-slate-400
        },
      });
    }),
  ],
}

module.exports = customConfig;