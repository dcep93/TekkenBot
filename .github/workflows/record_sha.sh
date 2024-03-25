#!/bin/bash

set -euo pipefail

printf "sha = '%s %s'\n" "$(git log -1)" "$(TZ='America/New_York' date)" >.github/workflows/recorded_sha.py
cat .github/workflows/recorded_sha.py
