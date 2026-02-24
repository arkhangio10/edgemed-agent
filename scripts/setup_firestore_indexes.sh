#!/usr/bin/env bash
set -euo pipefail

echo "=== Deploying Firestore rules and indexes ==="
cd "$(dirname "$0")/../firebase"

firebase deploy --only firestore:rules
echo "=== Firestore rules deployed ==="
