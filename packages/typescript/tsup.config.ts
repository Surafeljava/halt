import { defineConfig } from 'tsup';

export default defineConfig({
    entry: {
        index: 'src/index.ts',
        'adapters/express': 'src/adapters/express.ts',
        'adapters/next': 'src/adapters/next.ts',
    },
    format: ['esm', 'cjs'],
    dts: true,
    clean: true,
    sourcemap: true,
    splitting: false,
    treeshake: true,
});
