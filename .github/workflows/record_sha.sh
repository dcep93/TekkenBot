#!/bin/bash

set -euo pipefail

printf "sha = '%s'\n" "$(git log -1)" >.github/workflows/recorded_sha.txt
