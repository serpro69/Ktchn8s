#!/usr/bin/env bash

set -eu
set -o pipefail

export KUBECONFIG=./metal/kubeconfig.yaml

kubectl get applicationsets --namespace argocd
kubectl get applications --namespace argocd
kubectl get ingress --all-namespaces
