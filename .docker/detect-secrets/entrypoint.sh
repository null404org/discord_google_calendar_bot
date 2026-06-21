#!/bin/sh
set -e
# detect-secrets-hook calls `git rev-parse --show-toplevel` to resolve the
# repo root. Inside Docker the host's worktree .git file pointer is not
# accessible, so we create a throwaway git context and point it at the
# mounted working directory before exec-ing the real hook.
_tmp=$(mktemp -d)
trap 'rm -rf "$_tmp"' EXIT
git -C "$_tmp" init -q
exec env GIT_DIR="$_tmp/.git" GIT_WORK_TREE="$(pwd)" detect-secrets-hook "$@"
