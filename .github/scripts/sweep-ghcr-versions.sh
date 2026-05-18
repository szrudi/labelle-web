#!/usr/bin/env bash
# Delete GHCR container package versions AND the per-arch image
# and provenance attestation manifests they reference.
#
# GHCR does not cascade-delete manifest-list children, so a naive
# parent-only delete leaks ~4 untagged versions per multi-arch build
# (2 per-arch image manifests + 2 attestation manifests). This script
# walks each parent's manifest via the registry API and deletes the
# referenced child versions alongside the parent.
#
# Input:  parent version IDs on stdin, one per line.
# Env:    GH_TOKEN, OWNER, PACKAGE, IMAGE_NAME, GITHUB_ACTOR, SNAPSHOT
#         SNAPSHOT is a path to a JSON file shaped as
#         `[{id, name, tags}, ...]`, the output of the GHCR versions
#         API massaged into a stable form. Callers must produce it
#         AFTER any push that affects the same package, so digests
#         and IDs of any newly-pushed image are present and not
#         mistakenly enumerated as orphans.

set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN is required}"
: "${OWNER:?OWNER is required}"
: "${PACKAGE:?PACKAGE is required}"
: "${IMAGE_NAME:?IMAGE_NAME is required (e.g. owner/repo)}"
: "${GITHUB_ACTOR:?GITHUB_ACTOR is required}"
: "${SNAPSHOT:?SNAPSHOT path is required}"

# Pull-scope registry token, distinct from GH_TOKEN. The GitHub token
# is accepted as the password against the actor on GHCR's token
# endpoint, which returns a registry-scoped bearer.
REG_TOKEN=$(curl -fsSL -u "$GITHUB_ACTOR:$GH_TOKEN" \
  "https://ghcr.io/token?scope=repository:$IMAGE_NAME:pull&service=ghcr.io" \
  | jq -r .token)

TO_DELETE=$(mktemp)
CURL_ERR=$(mktemp)
trap 'rm -f "$TO_DELETE" "$CURL_ERR"' EXIT

while IFS= read -r PARENT_ID; do
  [ -z "$PARENT_ID" ] && continue
  echo "$PARENT_ID" >> "$TO_DELETE"

  DIGEST=$(jq -r --argjson id "$PARENT_ID" \
    '.[] | select(.id == $id) | .name' "$SNAPSHOT")
  if [ -z "$DIGEST" ] || [ "$DIGEST" = "null" ]; then
    echo "::warning::No digest in snapshot for version $PARENT_ID — children may leak"
    continue
  fi

  if MANIFEST=$(curl -fsSL \
      -H "Authorization: Bearer $REG_TOKEN" \
      -H "Accept: application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.manifest.v1+json,application/vnd.docker.distribution.manifest.v2+json" \
      "https://ghcr.io/v2/$IMAGE_NAME/manifests/$DIGEST" 2>"$CURL_ERR"); then
    # Single-arch manifests have no `.manifests` array; `?` makes this a no-op.
    echo "$MANIFEST" | jq -r '.manifests[]?.digest // empty' \
      | while IFS= read -r CHILD_DIGEST; do
          [ -z "$CHILD_DIGEST" ] && continue
          CHILD_ID=$(jq -r --arg d "$CHILD_DIGEST" \
            '.[] | select(.name == $d) | .id' "$SNAPSHOT")
          if [ -n "$CHILD_ID" ] && [ "$CHILD_ID" != "null" ]; then
            echo "$CHILD_ID" >> "$TO_DELETE"
          else
            echo "::warning::Child digest $CHILD_DIGEST not in snapshot — skipping"
          fi
        done
  elif grep -q "404" "$CURL_ERR"; then
    echo "::warning::Manifest $DIGEST already gone from registry — parent only"
  else
    echo "::error::Failed to fetch manifest $DIGEST:"
    cat "$CURL_ERR" >&2
    exit 1
  fi
done

if ! [ -s "$TO_DELETE" ]; then
  echo "No versions to delete"
  exit 0
fi
sort -u "$TO_DELETE" | while IFS= read -r VID; do
  [ -z "$VID" ] && continue
  echo "Deleting version $VID"
  gh api -X DELETE "/users/$OWNER/packages/container/$PACKAGE/versions/$VID"
done
