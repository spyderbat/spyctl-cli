#!/bin/bash

# Extend exclude is a regex string so adding multiple files
# would look like this:
# --extend-exclude "src/integrity_checks/dns\.py|src/content/sba\.py"
# Use backslashes to escape special characters.
CHECK_OPT=""
[ "$1" = "--check" ] && CHECK_OPT="--check"
black . $CHECK_OPT
