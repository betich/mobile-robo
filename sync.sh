#!/usr/bin/env bash
set -e

REMOTE_USER=kengvaris
REMOTE_HOST=100.69.19.59
REMOTE_PASS=014719
REMOTE_DIR='~/mobile-robo/'

SSHPASS="sshpass -p $REMOTE_PASS"

$SSHPASS ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR}"

$SSHPASS rsync -avz \
    -e "ssh -o StrictHostKeyChecking=no" \
    --exclude '.git/' \
    --exclude '.pio/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    ./ \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"
