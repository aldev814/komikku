# Bundled FlexibleAdapter

The repository under `../maven/` contains the AAR built from
[`arkon/FlexibleAdapter` commit c80135339bcff5f7f8c2c2380329dfc155b26232](https://github.com/arkon/FlexibleAdapter/tree/c80135339bcff5f7f8c2c2380329dfc155b26232).
JitPack currently cannot build this revision because the old `grabver:1.0.1`
build plugin requires `nu.studer:java-ordered-properties:1.0.1`, which its
configured repositories cannot resolve.

`build-dependency.patch` forces that buildscript dependency to `1.0.3`.
All 37 files under `flexible-adapter/src/` were verified unchanged against
the upstream source archive. This preserves the existing library implementation;
`1.0.3` is the build dependency's version, not a new FlexibleAdapter version.

The local artifact has a distinct version, `c8013533-local-properties1.0.3`.
The adjacent POM retains its RecyclerView runtime dependency and license.
`provenance.json` records the source revision and AAR SHA-256; `LICENSE`
preserves the upstream Apache license.

`settings.gradle.kts` resolves only the FlexibleAdapter module exclusively from
this checkout's `third-party/maven/`, and the version catalog selects this local
version. Normal Gradle commands, Android Studio Sync and Run use it without an
init script, user-level Maven repository, or files under ignored `dist/`.
These third-party files must be committed together with the Gradle changes.

## Rebuilding the AAR

1. Download and extract the source archive for the pinned commit above.
2. In the extracted source directory, apply this patch:
   `patch -p1 < /path/to/Shihon/third-party/flexible-adapter/build-dependency.patch`.
3. Use JDK 11, Android SDK Platform 30 and Build Tools 29.0.2. Set `ANDROID_HOME`
   or create an ignored `local.properties` with `sdk.dir` pointing to the SDK.
4. Run the upstream wrapper:
   `./gradlew :flexible-adapter:assembleRelease --configure-on-demand`.
5. The output is `flexible-adapter/build/outputs/aar/flexible-adapter-release.aar`.
   Copy it over the AAR in the local Maven repository only after verification,
   then update its recorded SHA-256. The old versioning plugin automatically
   updates generated build metadata, so a fresh build may have a different hash.

The bundled artifact passed `:app:assembleDebug` and APK signature verification
in the local build experiment. Device behavior was not tested by that experiment.
