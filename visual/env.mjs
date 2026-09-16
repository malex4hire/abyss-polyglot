// Where a driver points, supplied by scripts/visual.sh from stacks/manifest.yaml.
//
// A default would be worse than nothing here. These drivers used to fall back to a
// hard-coded origin, so running one with the variable unset silently drove whichever
// frontend happened to be on that port — reporting green about a stack nobody asked
// about. Missing configuration should stop, not guess.
export function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    console.error(
      `  ${name} is not set. These drivers take their target from the environment; ` +
      "run them through scripts/visual.sh, which reads it from the manifest.",
    );
    process.exit(2);
  }
  return value;
}
