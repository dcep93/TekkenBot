#!/bin/bash

set -euo pipefail

printf "sha = '%s %s'\n" "$(git log -1 --format=format:%H)" "$(TZ='America/New_York' date)" >.github/workflows/recorded_sha.py
cat .github/workflows/recorded_sha.py
mv .github/workflows/recorded_sha.py TekkenBot420/src/misc/recorded_sha.py
