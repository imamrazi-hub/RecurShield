#!/usr/bin/env bash
set -euo pipefail
: "${POSTGRES_PASSWORD:?Export POSTGRES_PASSWORD in terminal first}"
: "${IMAGE_REGISTRY:?Export IMAGE_REGISTRY e.g. Docker Hub username}"
# Important: ensure a default StorageClass exists or customize the PVC.
kubectl apply -f k8s/00-namespace-config.yaml
kubectl -n recurshield-prod create secret generic recurshield-secrets \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --from-literal=DATABASE_URL="postgresql+psycopg://recurshield:${POSTGRES_PASSWORD}@postgres:5432/recurshield" \
  --dry-run=client -o yaml | kubectl apply -f -
for file in k8s/01-postgres.yaml k8s/02-redis.yaml k8s/03-recommender.yaml k8s/04-api.yaml k8s/05-frontend.yaml; do
  sed "s@REPLACE_REGISTRY@${IMAGE_REGISTRY}@g" "$file" | kubectl apply -f -
done
kubectl -n recurshield-prod get pods,svc,pvc
