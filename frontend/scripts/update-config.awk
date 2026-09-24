#!/usr/bin/awk -f
# Usage: $0 SRC.json > DST.json
# Overwrite JSON properties from env vars of the same name (if set and non-empty),
# while preserving ALL original formatting (commas, spaces, blank lines).

BEGIN {
    FS  = "[[:space:]]*:[[:space:]]*"
    RS  = "[[:space:]]*[{,}]\n*"   # separators we want to re-emit
    ORS = ""                       # we’ll print RT ourselves
    OFS = ": "
}

{
    out = $0

    # Is this record a "key: value" pair?
    if (match($0, /^[[:space:]]*["'][A-Za-z0-9_]+["'][[:space:]]*:/)) {
        property = $1
        variable = property
        gsub(/^[[:space:]]*["']|["'][[:space:]]*$/, "", variable)

        # Consider env var set even if it's "0"
        if ((variable in ENVIRON) && ENVIRON[variable] != "") {
            val = ENVIRON[variable]
            gsub(/"/, "\\\"", val)
            out = property OFS "\"" val "\""
        } else {
            # Keep original value (handles colons inside the value)
            tmp = $0
            sub($1 FS, "", tmp)
            out = property OFS tmp
        }
    }

    # Re-emit the exact separator (comma/brace + spaces/newlines)
    printf "%s%s", out, RT
}

END {
    # nothing: last RT (possibly empty) already handled
}
