#!/usr/bin/env bash
set -euo pipefail
: "${RELEASE_TAG:?}" "${GH_REPO:?}" "${GITHUB_WORKSPACE:?}"
artifacts="$GITHUB_WORKSPACE/artifacts"
source_commit=$(python3 -c 'import json; print(json.load(open("../artifacts/build-metadata.json"))["source_commit"])')
[[ "$source_commit" =~ ^[a-f0-9]{40}$ ]]
[[ "$RELEASE_TAG" =~ ^ireader-v[0-9][A-Za-z0-9._+-]*-p[0-9]+$ ]]
git fetch "$artifacts/patched-source.bundle" refs/heads/ireader-release
[[ "$(git rev-parse FETCH_HEAD)" == "$source_commit" ]]
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
if [[ -n "$(git ls-remote --tags origin "refs/tags/$RELEASE_TAG")" ]]; then
  git fetch origin "refs/tags/$RELEASE_TAG"
  if [[ "$(git rev-parse 'FETCH_HEAD^{commit}')" != "$source_commit" ]]; then
    echo 'Existing release tag points to different source. Bump patch_revision; never overwrite a release tag.' >&2
    exit 1
  fi
else
  git tag -a "$RELEASE_TAG" "$source_commit" -m "Komikku iReader $RELEASE_TAG"
  git push origin "refs/tags/$RELEASE_TAG"
fi
# A draft is resumable; a published release is immutable to this automation.
if gh release view "$RELEASE_TAG" --json isDraft > "$RUNNER_TEMP/ireader-release.json" 2> "$RUNNER_TEMP/ireader-release-error.txt"; then
  if [[ "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["isDraft"])' "$RUNNER_TEMP/ireader-release.json")" != True ]]; then
    echo 'This release is already published; refusing to replace its assets.'
    exit 0
  fi
else
  # The API detector already established that the release is absent or a draft.
  gh release create "$RELEASE_TAG" --verify-tag --draft --title "Komikku iReader $RELEASE_TAG" --notes-file "$artifacts/RELEASE_NOTES.md"
fi
gh release upload "$RELEASE_TAG" "$artifacts"/*.apk "$artifacts/SHA256SUMS" "$artifacts/build-metadata.json" "$artifacts/ireader-patches.zip" --clobber
gh release edit "$RELEASE_TAG" --draft=false --latest --notes-file "$artifacts/RELEASE_NOTES.md"
