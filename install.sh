#!/bin/sh
set -eu

os=$(uname -s)
case "$os" in
Linux | Darwin) ;;
*)
    printf '%s is not supported\n' "$os" >&2
    exit 1
    ;;
esac

ref="${ORCHESTRA_REF-main}"

printf 'Checking operating system %s\n' "$os"
printf 'Checking for uv\n'
if ! command -v uv >/dev/null 2>&1; then
    printf 'Installing uv\n'
    curl -LsSf https://astral.sh/uv/install.sh | sh
    PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}"
    export PATH
fi

printf 'Installing orchestra from %s\n' "$ref"
from="git+https://github.com/andrewy1n/orchestra@${ref}"
if (: </dev/tty) >/dev/null 2>&1; then
    uvx --from "$from" orchestra install "$@" </dev/tty
else
    uvx --from "$from" orchestra install "$@" --yes
fi
