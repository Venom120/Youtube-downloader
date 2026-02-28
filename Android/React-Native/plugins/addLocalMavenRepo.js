const { withProjectBuildGradle } = require('@expo/config-plugins');

module.exports = function withAsyncStorageLocalRepo(config) {
  return withProjectBuildGradle(config, async (config) => {
    let contents = config.modResults.contents;

    const repoLine = '    // Local maven repo for @react-native-async-storage (provides org.asyncstorage.shared_storage)\n    maven { url "${rootDir}/../node_modules/@react-native-async-storage/async-storage/android/local_repo" }';

    if (!contents.includes('org.asyncstorage.shared_storage')) {
      // Try to insert after jitpack entry if present, otherwise after mavenCentral()
      if (contents.includes("maven { url 'https://www.jitpack.io' }")) {
        contents = contents.replace(
          "maven { url 'https://www.jitpack.io' }",
          "maven { url 'https://www.jitpack.io' }\n" + repoLine
        );
      } else if (contents.includes('mavenCentral()')) {
        contents = contents.replace(
          'mavenCentral()',
          'mavenCentral()\n' + repoLine
        );
      }

      config.modResults.contents = contents;
    }

    return config;
  });
};
