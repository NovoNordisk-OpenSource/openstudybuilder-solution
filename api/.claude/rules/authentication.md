---
paths:
  - common/auth/**
---
# Authentication & Authorization

- **OAuth 2.0** via Azure AD (configurable via `.env`)
- **RBAC**: Role-based access control (when `OAUTH_RBAC_ENABLED=true`)
- **MS Graph Integration**: Optional group discovery via Microsoft Graph API
- **Swagger UI Auth**: Separate `OAUTH_SWAGGER_APP_ID` for built-in docs authentication

See `doc/Auth.md` for Azure app-registration setup and the full env-var reference. Note that its claim of a "global dependency" requiring a token on almost all endpoints is **stale** — auth is applied per route, as below.

## Gating an endpoint

Two dependencies, always together, on the route decorator. There is no app-level auth dependency: a route with an empty `dependencies` list is public.

```python
from common.auth import rbac
from common.auth.dependencies import security

@router.get("/things", dependencies=[security, rbac.LIBRARY_READ])
```

`security` validates the token; the `rbac.*` constant checks roles. **Both are required** — an `rbac` constant alone silently skips token validation. Every real route in the codebase pairs them, `security` first.

## The role constants (`common/auth/rbac.py`)

Each is `Depends(RequiresAnyRole({...}))` over these six JWT roles: `Admin.Read`, `Admin.Write`, `Library.Read`, `Library.Write`, `Study.Read`, `Study.Write`.

| Constant | Grants access to holders of |
|---|---|
| `LIBRARY_READ` / `LIBRARY_WRITE` | the matching Library role — by far the most used |
| `STUDY_READ` / `STUDY_WRITE` | the matching Study role |
| `ADMIN_READ` / `ADMIN_WRITE` | the matching Admin role |
| `LIBRARY_WRITE_OR_STUDY_WRITE` | either write role |
| `LIBRARY_READ_OR_STUDY_READ` | either read role |
| `FEATURE_FLAG_READ` | any of `Admin.Read`, `Library.Read`, `Study.Read` |
| `ANY` | any of the four Library/Study roles |

- **`RequiresAnyRole` is OR, never AND.** For a combined gate use an existing `_OR_` constant; there is no AND primitive, so do not invent one.
- **`ANY` is not "public".** It still requires one of the four base roles. Only comments, msgraph, and jobs use it.
- **Do not infer the constant from the HTTP verb.** Library-vs-Study is the harder half of the choice and is not derivable from the path. Some Study endpoints also require `Library.Write` — a business rule documented in `doc/Auth.md`, not visible in code. **Copy the dependency from the nearest comparable route.**

## The local-dev trap — read before testing an auth change

With `OAUTH_ENABLED=false` (the default for local development), `security` binds to `dummy_user_auth` instead of `validate_token`, and the dummy user is granted **all six roles**.

Consequently **every endpoint works locally no matter which `rbac` constant you picked** — including the wrong one, and including none at all. Local manual testing cannot validate an authorization change. Verify with `pipenv run testauth`, which exercises the OAuth/RBAC paths, or in an OAuth-enabled environment.

`OAUTH_RBAC_ENABLED=false` is a second, independent switch: it replaces `RequiresAnyRole` with a no-op class, so role checks pass even when OAuth is on. Both flags log a startup `WARNING` when disabled.

## Config (`common/config.py`)

`oauth_enabled`, `oauth_rbac_enabled`, `oauth_metadata_url`, `oauth_api_app_id`, `oauth_api_app_secret`, `oauth_swagger_app_id`, `oauth_ui_app_id`, `dummy_user_id`. Env vars are the uppercased attribute names.

Token verification itself lives in `common/auth/jwk_service.py`: it fetches the provider's JWKS, caches the signing keys, and verifies the JWT signature plus `iss`/`aud`/expiry.
