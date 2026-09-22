#!/usr/bin/env bash
# Installs the git hooks that are located in the `.git-hooks` directory.
# This will overwrite already existing git hooks in your local `.git/hooks` directory.

# absolute path where this script is saved; without trailing slash
SCRIPT_PATH=$(
  cd "$(dirname "$0")" || exit
  pwd
)

ROOT_PATH="${SCRIPT_PATH}/.."

# remove all existing symbolic links
find "${ROOT_PATH}/.git/hooks" -type l -exec rm {} \;

# create the symbolic links in the .git/hooks directory
SUPPORTED_HOOKS="
applypatch-msg
commit-msg
fsmonitor-watchman
post-update
pre-applypatch
pre-commit
pre-merge-commit
prepare-commit-msg
pre-push
pre-rebase
pre-receive
update
"

cd "${ROOT_PATH}/.git/hooks" || exit 1

for hook in ${SUPPORTED_HOOKS}
do
  HOOK_FILE="${ROOT_PATH}/.git-hooks/${hook}"
  if test -f "${HOOK_FILE}"; then
    chmod +x "${HOOK_FILE}"
    ln -sf "../../.git-hooks/${hook}" "${hook}"
  fi
done

cd - || exit 1
