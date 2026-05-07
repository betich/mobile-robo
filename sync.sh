#!/usr/bin/env bash
set -e

REMOTE_USER=kengvaris
REMOTE_HOST=100.69.19.59
REMOTE_DIR='~/mobile-robo/'

ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR}"

rsync -avz \
    --exclude '.git/' \
    --exclude '.pio/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    ./ \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"
