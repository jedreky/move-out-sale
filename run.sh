#!/usr/bin/env bash
set -euo pipefail

uvicorn src.webapp:app --host 127.0.0.1 --port 8560 --reload
