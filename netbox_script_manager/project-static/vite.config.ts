import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    svelte(),
  ],
  build: {
    emptyOutDir: false,
    rollupOptions: {
      input: resolve(__dirname, './src/main.ts'),
      output: {
        format: 'iife',
        dir: resolve(__dirname, '../static/netbox_script_manager'),
        entryFileNames: 'main.js',
      },
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
});