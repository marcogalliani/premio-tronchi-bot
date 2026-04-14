# Kubernetes deployment

This folder contains a minimal Kubernetes deployment for the Telegram bot.

## Files

- `configmap.yaml`: non-secret settings
- `secret.example.yaml`: template for credentials
- `deployment.yaml`: single-replica bot Deployment
- `persistentvolumeclaim.yaml`: PVC for SQLite persistence
- `kustomization.yaml`: apply all resources with Kustomize

## Usage

1. Build and push the Docker image.
2. Create the Secret with `kubectl` or by applying your own manifest based on `secret.example.yaml`.
3. Update `deployment.yaml` image to your registry path.
4. Apply the config/deployment with:

```bash
kubectl apply -k k8s/
```

Example secret creation:

```bash
kubectl create secret generic premio-tronchi-secret \
	--from-literal=TELEGRAM_BOT_TOKEN=... \
	--from-literal=FANTACALCIO_COOKIE=...
```

## Notes

- The bot runs in polling mode.
- Keep `replicas: 1` to avoid duplicate Telegram polling.
- SQLite is stored at `/data/premio_tronchi.db` and persisted by `premio-tronchi-data` PVC.
- The default PVC uses `storageClassName: hostpath` (works on Docker Desktop). On other clusters, change this value to a StorageClass available in your environment.
