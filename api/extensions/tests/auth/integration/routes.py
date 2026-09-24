"""
This list must contain all routes of the Extensions API application as (path:str, method:str, required_roles:Set[str])
"""

ADMIN_WRITE = "Admin.Write"
ADMIN_READ = "Admin.Read"

ALL_ROUTES_METHODS_ROLES = (
    ("/prodex/extracts/active-substances", "POST", {ADMIN_WRITE}),
    ("/prodex/extracts/active-substances", "GET", {ADMIN_READ}),
    ("/prodex/extracts/active-substances/{uid}", "GET", {ADMIN_READ}),
    ("/prodex/loads/active-substances/{extract_uid}", "POST", {ADMIN_WRITE}),
    ("/prodex/loads/active-substances", "GET", {ADMIN_READ}),
    ("/prodex/loads/active-substances/{uid}", "GET", {ADMIN_READ}),
    ("/prodex/extracts/medicinal-products", "POST", {ADMIN_WRITE}),
    ("/prodex/extracts/medicinal-products", "GET", {ADMIN_READ}),
    ("/prodex/extracts/medicinal-products/{uid}", "GET", {ADMIN_READ}),
    ("/prodex/loads/medicinal-products/{extract_uid}", "POST", {ADMIN_WRITE}),
    ("/prodex/loads/medicinal-products", "GET", {ADMIN_READ}),
    ("/prodex/loads/medicinal-products/{uid}", "GET", {ADMIN_READ}),
    ("/hello/nodes-count", "GET", {ADMIN_READ}),
)
