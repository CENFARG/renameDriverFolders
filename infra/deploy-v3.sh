#!/bin/bash
# deploy-v3.sh — Parallel deployment script for v3 services
# Deploys v3 alongside v2 with optional traffic splitting
#
# Usage:
#   ./infra/deploy-v3.sh api     # Deploy API server v3 only
#   ./infra/deploy-v3.sh worker  # Deploy worker v3 only
#   ./infra/deploy-v3.sh all     # Deploy both v3 services
#   ./infra/deploy-v3.sh traffic # Shift 10% traffic to v3

set -euo pipefail

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
REGION="us-central1"
API_SERVICE="renombradorarchivosgdrive-api-server-v3"
WORKER_SERVICE="renombradorarchivosgdrive-worker-v3"
SA="702567224563-compute@developer.gserviceaccount.com"

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: No GCP project configured. Run 'gcloud config set project <PROJECT_ID>'"
    exit 1
fi

deploy_api() {
    echo "==> Building API Server v3..."
    gcloud builds submit \
        --config services/api-server-v3/cloudbuild.yaml \
        --timeout 1200s

    echo "==> API Server v3 deployed to $API_SERVICE"
}

deploy_worker() {
    echo "==> Building Worker v3..."
    gcloud builds submit \
        --config services/worker-v3/cloudbuild.yaml \
        --timeout 1200s

    echo "==> Worker v3 deployed to $WORKER_SERVICE"
}

shift_traffic() {
    local percent="${1:-10}"
    echo "==> Shifting $percent% traffic to $API_SERVICE..."
    gcloud run services update-traffic "$API_SERVICE" \
        --to-revisions "LATEST=$percent" \
        --region "$REGION"

    echo "==> Traffic shifted. Monitor and increase gradually."
    echo "    To shift more: ./infra/deploy-v3.sh traffic 25"
    echo "    To go 100%:    ./infra/deploy-v3.sh traffic 100"
}

case "${1:-help}" in
    api)
        deploy_api
        ;;
    worker)
        deploy_worker
        ;;
    all)
        deploy_api
        deploy_worker
        ;;
    traffic)
        shift_traffic "${2:-10}"
        ;;
    help|*)
        echo "Usage: $0 {api|worker|all|traffic [percent]}"
        echo ""
        echo "Commands:"
        echo "  api           Build and deploy API Server v3"
        echo "  worker        Build and deploy Worker v3"
        echo "  all           Build and deploy both v3 services"
        echo "  traffic [N]   Shift N% traffic to v3 (default: 10)"
        ;;
esac
