#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
for t in test_*.py; do echo "=== $t ==="; python3 "$t"; echo; done
