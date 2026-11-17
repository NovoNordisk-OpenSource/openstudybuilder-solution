"""Every route of the Standards Import API and the roles it requires.

Kept by hand on purpose: a route appearing here without anyone meaning to add it is
the thing worth noticing. `test_route_protection` holds this and the app to each other.
"""

IMPORT = "Library.Import"

# One role gates the whole app, so these two sets are equal today. They are still kept
# apart because the table below is also a statement of what each route *does*, and
# because a narrower read role would land here rather than on twenty-odd decorators.
# The consequence to know: the third column can no longer catch a read route wired to
# the write dependency. What the table still catches is a route that is new, gone,
# renamed, or behind no role at all.
READ = {IMPORT}
WRITE = {IMPORT}

# Deliberately behind no role: the container HEALTHCHECK calls it without a token.
# Anything added here is open to every caller, so it needs a reason as good as this one.
PUBLIC_ROUTES = {("/system/healthcheck", "GET")}

ALL_ROUTES_METHODS_ROLES = (
    ("/packages/files", "POST", WRITE),
    ("/packages/files", "GET", READ),
    ("/packages/files/diff-summaries", "GET", READ),
    ("/packages/files/{catalogue}/previous-release", "GET", READ),
    ("/packages/files/{catalogue}/diff", "GET", READ),
    ("/packages/files/{catalogue}/history/{concept_type}/{concept_id}", "GET", READ),
    # Writes the releases it found, so it is a write route despite only reading CDISC.
    ("/packages/discover", "POST", WRITE),
    ("/effective-dates", "GET", READ),
    ("/effective-dates/{effective_date}", "GET", READ),
    ("/effective-dates/{effective_date}/pairings", "POST", WRITE),
    ("/effective-dates/{effective_date}/pairings", "GET", READ),
    ("/effective-dates/{effective_date}/changelog", "POST", WRITE),
    ("/effective-dates/{effective_date}/changelog", "GET", READ),
    ("/effective-dates/{effective_date}/analysis", "POST", WRITE),
    ("/effective-dates/{effective_date}/analysis", "GET", READ),
    ("/effective-dates/{effective_date}/sponsor-impact", "POST", WRITE),
    ("/effective-dates/{effective_date}/sponsor-impact", "GET", READ),
    ("/effective-dates/{effective_date}/preview", "GET", READ),
    ("/effective-dates/{effective_date}/import", "POST", WRITE),
    ("/resolution-strategies", "GET", READ),
    ("/inconsistencies", "GET", READ),
    ("/inconsistencies/{uid}", "GET", READ),
    ("/inconsistencies/{uid}/resolution", "POST", WRITE),
    ("/inconsistencies/{uid}/resolution", "DELETE", WRITE),
    ("/resolution-rules", "GET", READ),
    ("/resolution-rules", "POST", WRITE),
    ("/resolution-rules/{uid}", "GET", READ),
    ("/resolution-rules/{uid}", "PATCH", WRITE),
    ("/resolution-rules/{uid}", "DELETE", WRITE),
    ("/config/catalogue-priority", "GET", READ),
    ("/config/catalogue-priority", "PUT", WRITE),
    ("/config/mandatory-catalogues", "PUT", WRITE),
    ("/config/expected-workbooks", "PUT", WRITE),
    ("/config/import-enabled", "GET", READ),
    ("/config/import-enabled", "PUT", WRITE),
    ("/jobs", "GET", READ),
    ("/jobs/{uid}", "GET", READ),
    ("/type-descriptions", "GET", READ),
    ("/effective-dates/{effective_date}/dashboard", "GET", READ),
    ("/effective-dates/{effective_date}/codelists", "GET", READ),
    ("/effective-dates/{effective_date}/codelists/{codelist_id}", "GET", READ),
    ("/effective-dates/{effective_date}/terms", "GET", READ),
    ("/effective-dates/{effective_date}/terms/{concept_id}", "GET", READ),
    ("/effective-dates/{effective_date}/codelists/{codelist_id}/review", "POST", WRITE),
    (
        "/effective-dates/{effective_date}/codelists/{codelist_id}/review",
        "DELETE",
        WRITE,
    ),
)
