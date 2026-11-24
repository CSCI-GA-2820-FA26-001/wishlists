# Deploy Wishlists to OpenShift (#71)

Run these commands in the project's **Dev Container Bash**, from `/app`.
Use your own Red Hat Developer Sandbox project. This is a disposable development
deployment: the existing BDD Background deletes every wishlist in its target.

The manifests keep PostgreSQL 16, database `wishlists`, user `postgres`, and the
project's production Dockerfile. The database uses a 1 GiB PVC and a `PGDATA`
subdirectory so the OpenShift-assigned UID can initialize the data directory.
The complete `DATABASE_URI` comes from a Secret. The service is exposed through
an HTTPS Route with edge TLS termination.

`k8s/` and its local `make cluster/build/push/deploy` workflow remain separate.
The BuildConfig below is a manual bootstrap build for this Story; the Tekton
tasks and webhook belong to their own Stories.

## 1. Confirm the source and project

Log in using **Copy login command** in your OpenShift Console. Keep that token
local. Select your actual `<user>-dev` project with `oc project`, then run:

```bash
cd /app
git status --short --branch
oc whoami
oc project
OPENSHIFT_NAMESPACE="$(oc project -q)"
IMAGE_TAG="$(git rev-parse HEAD)"
printf 'Project: %s\nSource: %s\n' "$OPENSHIFT_NAMESPACE" "$IMAGE_TAG"
oc get pods,pvc,svc,route,buildconfig,imagestream
```

Stop if the project or source is unexpected. Check any existing resources named
`wishlists` or `wishlists-postgres` before applying these manifests. The image
tag must identify the source being uploaded; commit source changes before a
later rebuild. The initial #71 changes add deployment manifests and documentation
without changing the application source or Dockerfile.

## 2. Create the database Secret once

```bash
oc get secret wishlists-postgres-secret --ignore-not-found
```

On a fresh deployment, when that Secret does not exist, run:

```bash
oc process --local -f openshift/database-secret.yaml \
  | oc create -n "$OPENSHIFT_NAMESPACE" -f -
```

This generates a random password without printing it or saving credentials in the
repository. Reuse the existing Secret on subsequent deployments. Generating a
new password does not change the password stored in an existing PostgreSQL PVC.
Do not commit a rendered Secret or export its values into a PR or log.

## 3. Validate and deploy PostgreSQL

```bash
oc apply -n "$OPENSHIFT_NAMESPACE" --dry-run=server -f openshift/postgres.yaml
oc apply -n "$OPENSHIFT_NAMESPACE" -f openshift/postgres.yaml
oc rollout status -n "$OPENSHIFT_NAMESPACE" statefulset/wishlists-postgres --timeout=300s
oc get pods,pvc,svc -n "$OPENSHIFT_NAMESPACE"
oc exec -n "$OPENSHIFT_NAMESPACE" wishlists-postgres-0 -- sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" psql -h wishlists-postgres -U postgres -d wishlists -v ON_ERROR_STOP=1 -c "SELECT current_database();"'
```

Expect PostgreSQL to be Ready, PVC `postgres-data-wishlists-postgres-0` to be
Bound, and the authenticated query to return `wishlists`. A default StorageClass
must be available in the Sandbox. Do not hard-code a UID, use an `anyuid` SCC,
or delete the PVC to work around a startup failure; inspect the Pod events and
logs first.

## 4. Build the application in OpenShift

```bash
oc process --local -f openshift/build.yaml -p IMAGE_TAG="$IMAGE_TAG" \
  | oc apply -n "$OPENSHIFT_NAMESPACE" --dry-run=server -f -
oc process --local -f openshift/build.yaml -p IMAGE_TAG="$IMAGE_TAG" \
  | oc apply -n "$OPENSHIFT_NAMESPACE" -f -
oc start-build wishlists -n "$OPENSHIFT_NAMESPACE" --from-dir=. --follow --wait
oc get istag "wishlists:$IMAGE_TAG" -n "$OPENSHIFT_NAMESPACE"
```

This uploads the local source and builds the existing `Dockerfile`; a Git push
is not required for this manual build. The resulting image is stored in this
project's internal registry. Stop if the build fails. Sandbox permissions and
quotas must allow Docker-strategy builds and their build Pods. This BuildConfig
has no automatic trigger or GitHub webhook.

## 5. Deploy Wishlists and its Route

```bash
oc process --local -f openshift/deployment.yaml \
  -p NAMESPACE="$OPENSHIFT_NAMESPACE" -p IMAGE_TAG="$IMAGE_TAG" \
  | oc apply -n "$OPENSHIFT_NAMESPACE" --dry-run=server -f -
oc process --local -f openshift/deployment.yaml \
  -p NAMESPACE="$OPENSHIFT_NAMESPACE" -p IMAGE_TAG="$IMAGE_TAG" \
  | oc apply -n "$OPENSHIFT_NAMESPACE" -f -
oc rollout status -n "$OPENSHIFT_NAMESPACE" deployment/wishlists --timeout=300s
oc get pods,pvc,svc,route -n "$OPENSHIFT_NAMESPACE"
BASE_URL="https://$(oc get route wishlists -n "$OPENSHIFT_NAMESPACE" -o jsonpath='{.spec.host}')"
printf 'Wishlist URL: %s\n' "$BASE_URL"
curl --fail --silent --show-error --include "$BASE_URL/health"
```

Expect HTTP `200` and JSON `{"status":"OK"}`. Open `$BASE_URL/` to reach
Wishlist Admin. The Route hostname is allocated by this cluster; do not use the
hostname from another student's project or a lecture screenshot.

## 6. Verify the database and persistence through the application

1. In Wishlist Admin, create a uniquely named test wishlist and record its ID.
   Clear the form and use **Retrieve** beside the ID field to read it back.
   Record its fields. **Search** filters the list by customer/name, not ID.
2. Record both running Pod UIDs, then restart the database and application:

```bash
oc get pods -n "$OPENSHIFT_NAMESPACE" --field-selector=status.phase=Running -o 'custom-columns=NAME:.metadata.name,UID:.metadata.uid'
oc rollout restart statefulset/wishlists-postgres -n "$OPENSHIFT_NAMESPACE"
oc rollout status -n "$OPENSHIFT_NAMESPACE" statefulset/wishlists-postgres --timeout=300s
oc rollout restart deployment/wishlists -n "$OPENSHIFT_NAMESPACE"
oc rollout status -n "$OPENSHIFT_NAMESPACE" deployment/wishlists --timeout=300s
oc get pods -n "$OPENSHIFT_NAMESPACE" --field-selector=status.phase=Running -o 'custom-columns=NAME:.metadata.name,UID:.metadata.uid'
oc get pvc postgres-data-wishlists-postgres-0 -n "$OPENSHIFT_NAMESPACE"
curl --fail --silent --show-error --include "$BASE_URL/health"
```

3. Confirm the Pod UIDs changed and the PVC remained Bound. Reload Wishlist Admin
   and retrieve the same ID; its saved fields must be unchanged. Delete only that
   test wishlist after verification. Do not delete the PVC.

Health alone does not prove the database connection or persistence. Record the
actual results of both checks separately. Run full BDD only against a deployment
whose entire Wishlist dataset may be discarded; keep `BASE_URL` pointed at that
deployment and do not share its database with concurrently running tests.

## 7. Run BDD against the deployment

After the persistence check, run the complete suite from the Dev Container:

```bash
BASE_URL="$BASE_URL" behave --format progress
```

The existing Background deletes every wishlist in this deployment and loads its
fixtures. The persistence probe's ID will therefore be removed as part of this
test setup. Record the actual feature/scenario/step results with the tested
application SHA and image digest; an older run is not verification of a new image.

## Troubleshooting and evidence

```bash
oc get events -n "$OPENSHIFT_NAMESPACE" --sort-by=.lastTimestamp
oc logs -n "$OPENSHIFT_NAMESPACE" wishlists-postgres-0
oc logs -n "$OPENSHIFT_NAMESPACE" deployment/wishlists -c wishlists
```

For image build failures, use the failed Build's logs (`oc logs build/<name>`).
For permissions or admission failures, retain the exact error and resource type;
do not request broad cluster-admin privileges as a default fix. GitHub repository
Admin permission is needed later for the webhook, not for this manual deployment.

For the PR, record the full source SHA, namespace, application image digest,
Route URL, health response, authenticated database query, persistence result,
commands, environment, and date. The Pod's `imageID` must match the image from
the completed Build. A later source change requires a new build and verification.

These commands are verification instructions, not evidence that OpenShift
deployment, image build, persistence, or the existing test suites have passed.
