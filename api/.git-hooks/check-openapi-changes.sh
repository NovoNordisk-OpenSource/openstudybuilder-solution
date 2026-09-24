#!/usr/bin/env bash

check_for_changes() {
    local dir=$1
    local exclude_patterns=$2

    # Get the list of staged files
    local changed_files=$(git diff --cached --name-only)

    # Exit if openapi.json is in the changed files
    if echo "$changed_files" | grep -q "openapi.json"; then
        exit 0
    fi

    echo "Checking for changes in $dir..."

    # Filter changed files within the specified directory
    local dir_changed_files=$(echo "$changed_files" | grep "^$dir")

    # Exclude specific files or directories
    local filtered_files=$(echo "$dir_changed_files" | grep -vE "$exclude_patterns")

    # If there are any files left, ask user to generate openapi.json
    if [[ -n "$filtered_files" ]]; then
        echo "⚠️  Detected changes in $dir:"
        echo "$filtered_files"
        printf "\nPlease regenerate the OpenAPI documentation.\n"
        exit 1
    fi
}

# Watch for changes in specific directories
check_for_changes "clinical_mdr_api/models/" "utils.py|validators.py"
check_for_changes "clinical_mdr_api/routers/" "__init__.py"
