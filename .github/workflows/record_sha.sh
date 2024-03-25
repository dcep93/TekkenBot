#!/bin/bash

set -euo pipefail

printf "sha = '%s %s'\n" "$(git log -1)" "$(TZ='America/New_York' date)" | tee /dev/tty >.github/workflows/recorded_sha.py
