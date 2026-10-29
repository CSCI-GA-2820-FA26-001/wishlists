# Local PostgreSQL (#40)

These manifests provide PostgreSQL 16, database `wishlists`, user `postgres`,
one replica, and a 1 GiB ReadWriteOnce PVC. The internal ClusterIP endpoint is
`wishlists-postgres:5432`; it is accessible from Pods in the default namespace.
Application deployment and database connection wiring belong to #38.

## Prerequisites

Use a running local k3d cluster, `kubectl`, OpenSSL, and a default StorageClass
(normally K3S `local-path`). The repository's `make cluster` creates `nyu-devops`
when needed. Confirm the intended context before making changes:

```sh
kubectl config use-context k3d-nyu-devops
kubectl config current-context
kubectl get nodes
kubectl get storageclass
```

Continue only when a node is Ready and a default StorageClass is available.
The commands below explicitly use the default namespace. Check for existing
resources and stop on conflicts rather than overwriting another deployment:

```sh
kubectl -n default get service,statefulset,secret wishlists-postgres wishlists-postgres-secret --ignore-not-found
kubectl -n default get pvc postgres-data-wishlists-postgres-0 --ignore-not-found
```

## Create the Secret and deploy

Generate the password directly into the Secret's input stream; do not print it,
put it in command arguments, or save generated Secret YAML or credentials in Git.
Run this only when the Secret does not already exist:

```sh
openssl rand -hex 24 | tr -d '\n' | kubectl -n default create secret generic wishlists-postgres-secret --from-file=POSTGRES_PASSWORD=/dev/stdin
kubectl -n default get secret wishlists-postgres-secret
kubectl -n default apply --dry-run=client -f k8s/postgres/
kubectl -n default apply -f k8s/postgres/
kubectl -n default rollout status statefulset/wishlists-postgres --timeout=180s
kubectl -n default get statefulset wishlists-postgres
kubectl -n default get pods -l app=wishlists-postgres
kubectl -n default get pvc postgres-data-wishlists-postgres-0
kubectl -n default get service wishlists-postgres
```

Expect StatefulSet 1/1 Ready, Pod `wishlists-postgres-0` Running and Ready,
PVC `postgres-data-wishlists-postgres-0` Bound, and Service ClusterIP on 5432.
Recreate the Secret when provisioning a fresh cluster. Replacing this Secret
**does not change the password stored in an existing PostgreSQL data volume**.

## Verify access through the Service

The password is supplied from the container's Secret-backed environment:

```sh
kubectl -n default exec wishlists-postgres-0 -- sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -h wishlists-postgres -U postgres -d wishlists -v ON_ERROR_STOP=1 -c "SELECT current_database();"'
```

Expect `wishlists`. Do not proceed until this succeeds.

## Verify persistence after Pod recreation

On a fresh database, create the verification table and insert a row:

```sh
kubectl -n default exec -i wishlists-postgres-0 -- sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -h wishlists-postgres -U postgres -d wishlists -v ON_ERROR_STOP=1' <<'SQL'
CREATE TABLE persistence_check (id INTEGER PRIMARY KEY, value TEXT NOT NULL);
INSERT INTO persistence_check VALUES (1, 'persisted');
SQL
kubectl -n default get pod wishlists-postgres-0 -o jsonpath='{.metadata.uid}{"\n"}'
kubectl -n default delete pod wishlists-postgres-0
kubectl -n default rollout status statefulset/wishlists-postgres --timeout=180s
kubectl -n default get pod wishlists-postgres-0 -o jsonpath='{.metadata.uid}{"\n"}'
kubectl -n default get pods -l app=wishlists-postgres
kubectl -n default get pvc postgres-data-wishlists-postgres-0
kubectl -n default exec wishlists-postgres-0 -- sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -h wishlists-postgres -U postgres -d wishlists -v ON_ERROR_STOP=1 -c "SELECT id, value FROM persistence_check;"'
```

Confirm that the Pod UID changed, the PVC remains Bound, and the query returns
`1 | persisted`. The table is deliberately retained; rerunning its creation
will fail if it already exists. Do not delete the PVC. Leave the database and
PVC running for the next developer.

## Validation status

This change was checked offline for YAML parsing, required resource fields,
matching selectors, Secret references, and storage configuration. The shell
examples were syntax checked. Kubernetes API validation, deployment readiness,
authenticated Service access, and Pod-recreation persistence have **not been run**.
The commands above are instructions for those remaining live checks.
