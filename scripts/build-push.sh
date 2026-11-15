#!/usr/bin/env bash
set -euo pipefail
: "${IMAGE_REGISTRY:?Export Docker Hub username or registry namespace}"
for component in api recommender frontend; do
  docker buildx build --platform linux/amd64,linux/arm64 \
    -t "${IMAGE_REGISTRY}/recurshield-${component}:v0.1" \
    --push "./${component}"
done
