const { withGradleProperties } = require('@expo/config-plugins');

module.exports = function withReactNativeArchitectures(config) {
  return withGradleProperties(config, (config) => {
    const props = config.modResults;
    const ensureProperty = (key, value) => {
      const idx = props.findIndex((p) => p.type === 'property' && p.key === key);
      if (idx !== -1) {
        props[idx].value = value;
      } else {
        props.push({ type: 'property', key, value });
      }
    };

    ensureProperty('reactNativeArchitectures', 'arm64-v8a,x86_64');
    // Avoid CMake/prefab failures from armv7-only native artifacts (e.g. mmkv mismatch)
    ensureProperty('newArchEnabled', 'false');
    // Disable parallel builds to prevent file locking issues on Windows
    ensureProperty('org.gradle.parallel', 'false');

    config.modResults = props;
    return config;
  });
};
