#!/usr/bin/env bash
set -e

REMOTE_USER=kengvaris
REMOTE_HOST=100.69.19.59
REMOTE_DIR=~/mobile-robo/controller/

rsync -avz --exclude '__pycache__' --exclude '*.pyc' \
    controller/ \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"
