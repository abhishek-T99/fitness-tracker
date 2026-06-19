/** @type {import('@babel/core').ConfigAPI} */
module.exports = {
  plugins: [
    // Vite-specific syntax not available in Jest's Node environment.
    // Replace `import.meta` with `({ env: {} })` so `import.meta.env.VITE_*`
    // evaluates to `undefined` and falls through to the code's own defaults.
    function replaceImportMeta() {
      return {
        visitor: {
          MetaProperty(path) {
            if (
              path.node.meta.name === "import" &&
              path.node.property.name === "meta"
            ) {
              path.replaceWithSourceString("({ env: {} })");
            }
          },
        },
      };
    },
  ],
  presets: [
    ["@babel/preset-env", { targets: { node: "current" }, modules: "commonjs" }],
    ["@babel/preset-react", { runtime: "automatic" }],
  ],
};
