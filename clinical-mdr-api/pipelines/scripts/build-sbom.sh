#!/bin/bash
#
# Builds SBOM.md form installed Python packages their licenses to stdout
#

set -e

FALLBACK_LICENSE_DIR="$(dirname "$0")/../../doc/sbom/licenses"


fatal() {
    log "$*"
    exit 1
}

log() {
    echo "$*" 1>&2
}

temp_files=""
exit_hook() {
    rm -f -- $temp_files
}
trap exit_hook EXIT


if [ -n "$VIRTUAL_ENV" ]; then
    search_dirs="$VIRTUAL_ENV"
else
    search_dirs="$(python3 -m site --user-site)"
fi

[ -n "$search_dirs" ] || fatal "Can't find Python package directory"
[ -d "$search_dirs" ] || fatal "Python package directory doesn't exist: $search_dirs"
[ -n "$FALLBACK_LICENSE_DIR" ] || fatal "Fallback license directory not set"
[ -d "$FALLBACK_LICENSE_DIR" ] || fatal "Fallback license directory not exists: $FALLBACK_LICENSE_DIR"
[ -r "$FALLBACK_LICENSE_DIR" ] || fatal "Fallback license directory is not readable: $FALLBACK_LICENSE_DIR"


echo -e '\xEF\xBB\xBF'  # UTF-8 BOM
cat <<EOF
## Installed packages

EOF

package_list="$(mktemp)" || fatal "Couldn't get a temporary file"
temp_files="$temp_files $package_list"
pip list --format freeze > "$package_list"

{
    echo "|            Package             |       Version        |"
    echo "|--------------------------------|----------------------|"
    awk -F == '{ printf("| %-30s | %-20s |\n", $1, $2) }' "$package_list"
}


cat <<EOF


## Third-party package licenses
EOF

all_license_files="$(mktemp)" || fatal "couldn't get a temporary file"
temp_files="$temp_files $all_license_files"
find "$search_dirs" -iregex ".*\(licen[cs]e\|copying\).*" -type f ! -iname "*.py" ! -iname "*.pyc" > "$all_license_files"

while IFS="=" read -a line; do
    # actually this can find multiple files
    license_files="$(grep -E "/${line[0]//-/_}(-${line[2]//./\\.}\\.dist-info)?/" $all_license_files)" || true

    [ -n "$license_files" ] || {
        license_files="$(find "$FALLBACK_LICENSE_DIR" -iname "${line[0]}" -or -iname "${line[0]}.*")"
    }

    [ -n "$license_files" ] || {
        log "WARNING: License file not found for package: ${line[0]}"
        continue
    }

    log "Package ${line[0]} license files: $license_files"
    cat <<EOF


---

### License for 3rd party library ${line[0]}

EOF
    cat $license_files

done < "$package_list"

exit 0
