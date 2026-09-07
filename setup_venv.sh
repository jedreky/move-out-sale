#!/usr/bin/env bash
set -euo pipefail

python3.13 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
