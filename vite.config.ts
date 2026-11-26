import {defineConfig} from 'vite';
import canvasCommons from '@canvas-commons/vite-plugin';

export default defineConfig({
  plugins: [
    canvasCommons({
      project: ['./src/project.ts', './src/vinixedz.ts'],
    }),
  ],
});
