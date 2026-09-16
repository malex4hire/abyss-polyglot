import { defineConfig } from "vite";

/**
 * No Angular build plugin, in any mode.
 *
 * Under test its transform emitted nothing for a plain spec file. Under build it emitted
 * nothing at all: a transform count in the single digits and a 711-byte bundle containing
 * only the modulepreload polyfill, with no error. Both failures are silent, which is the
 * worst property a build step can have.
 *
 * esbuild compiles the decorators and the app runs with Angular's JIT compiler, imported
 * by main.ts. The trade is compiling templates in the browser at startup, which costs
 * milliseconds on a demo that runs on one laptop, against a build that produces nothing
 * and says it succeeded.
 */
export default defineConfig({
  server: { host: "0.0.0.0", port: 8080 },
  esbuild: { target: "es2022" },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/zoneless-setup.ts"],
    include: ["src/test/**/*.spec.ts"],
  },
});
