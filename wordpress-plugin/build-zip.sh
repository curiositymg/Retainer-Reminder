#!/usr/bin/env bash
# Package the plugin into an installable zip next to this script.
set -euo pipefail

cd "$(dirname "$0")"

version="$(grep -m1 '^ \* Version:' ghl-directory/ghl-directory.php | awk '{print $3}')"
output="ghl-directory-${version}.zip"

rm -f "$output"
zip -rq "$output" ghl-directory \
	-x '*.DS_Store' '*/node_modules/*' '*/.git/*'

echo "Wrote $output"
