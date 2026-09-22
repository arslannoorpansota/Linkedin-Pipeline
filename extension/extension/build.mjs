import * as esbuild from 'esbuild';
import { cp, mkdir, rm } from 'node:fs/promises';

const watch = process.argv.includes('--watch');
const outdir = 'dist';

await rm(outdir, { recursive: true, force: true });
await mkdir(outdir, { recursive: true });

const ctx = await esbuild.context({
  entryPoints: {
    'background': 'src/background/index.ts',
    'content': 'src/content/index.ts',
    'injected': 'src/content/injected.ts',
    'dashboard': 'src/dashboard/main.ts',
  },
  bundle: true,
  format: 'iife',
  target: 'chrome120',
  outdir,
  sourcemap: watch ? 'inline' : false,
  minify: !watch,
  logLevel: 'info',
});

await cp('manifest.json', `${outdir}/manifest.json`);
await cp('src/dashboard/index.html', `${outdir}/dashboard.html`);

if (watch) { await ctx.watch(); console.log('watching...'); }
else { await ctx.rebuild(); await ctx.dispose(); }
