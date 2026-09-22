#!/usr/bin/env bash
# Deploy only Pantry Relay's dedicated resources. Requires existing infrastructure.
set -euo pipefail
cd "$(dirname "$0")/.."
PANTRY_PROJECT="${PANTRY_PROJECT:-gen-lang-client-0444960702}"
PANTRY_REGION="${PANTRY_REGION:-us-central1}"
PANTRY_SERVICE="pantry-relay-api"
PANTRY_SITE="pantryrelay"
PANTRY_IMAGE="$PANTRY_REGION-docker.pkg.dev/$PANTRY_PROJECT/pantry-relay/api:$(git rev-parse --short HEAD)-$(date +%Y%m%d%H%M%S)"
PANTRY_ACCOUNT="pantry-relay-api@$PANTRY_PROJECT.iam.gserviceaccount.com"
PANTRY_CONNECTION="$PANTRY_PROJECT:$PANTRY_REGION:pantry-relay-db"
PANTRY_PROJECT_NUMBER="$(gcloud projects describe "$PANTRY_PROJECT" --format='value(projectNumber)')"
PANTRY_HOSTS="$PANTRY_SITE.web.app,$PANTRY_SITE.firebaseapp.com,$PANTRY_SERVICE-$PANTRY_PROJECT_NUMBER.$PANTRY_REGION.run.app"
(cd frontend && npm ci && npm run build)
gcloud builds submit --project="$PANTRY_PROJECT" --tag="$PANTRY_IMAGE" --quiet
gcloud run deploy "$PANTRY_SERVICE" --project="$PANTRY_PROJECT" --region="$PANTRY_REGION" \
  --image="$PANTRY_IMAGE" --service-account="$PANTRY_ACCOUNT" --allow-unauthenticated \
  --port=8000 --cpu=1 --memory=512Mi --min=0 --max=2 --concurrency=8 --timeout=60 \
  --add-cloudsql-instances="$PANTRY_CONNECTION" \
  --set-secrets=PANTRY_DATABASE=pantry-relay-database:latest \
  --set-env-vars="^|^PANTRY_ENV=production|PANTRY_COOKIE_SECURE=true|PANTRY_DEMO_ENABLED=true|PANTRY_DEMO_ONLY=false|PANTRY_ALLOW_PUBLIC_DEMO=true|PANTRY_ALLOWED_HOSTS=$PANTRY_HOSTS|PANTRY_TRUSTED_ORIGINS=https://$PANTRY_SITE.web.app,https://$PANTRY_SITE.firebaseapp.com" \
  --quiet
PANTRY_API_URL="$(gcloud run services describe "$PANTRY_SERVICE" --project="$PANTRY_PROJECT" --region="$PANTRY_REGION" --format='value(status.url)')"
PANTRY_API_HOST="${PANTRY_API_URL#https://}"
if [[ ",$PANTRY_HOSTS," != *",$PANTRY_API_HOST,"* ]]; then
  gcloud run services update "$PANTRY_SERVICE" --project="$PANTRY_PROJECT" --region="$PANTRY_REGION" \
    --update-env-vars="^|^PANTRY_ALLOWED_HOSTS=$PANTRY_HOSTS,$PANTRY_API_HOST" --quiet
fi
npx --yes firebase-tools@15.30.2 deploy --only hosting --project="$PANTRY_PROJECT" --non-interactive
curl --fail --silent --show-error "https://$PANTRY_SITE.web.app/api/health"
printf '\nDeployed: https://%s.web.app\n' "$PANTRY_SITE"
