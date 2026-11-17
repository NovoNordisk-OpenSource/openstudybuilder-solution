"""Common Role-Based Access Control dependencies as re-usable constants"""

from fastapi import Depends

from common.auth.dependencies import RequiresAnyRole

ADMIN_READ = Depends(RequiresAnyRole({"Admin.Read"}))
ADMIN_WRITE = Depends(RequiresAnyRole({"Admin.Write"}))
LIBRARY_READ = Depends(RequiresAnyRole({"Library.Read"}))
LIBRARY_WRITE = Depends(RequiresAnyRole({"Library.Write"}))
STUDY_READ = Depends(RequiresAnyRole({"Study.Read"}))
STUDY_WRITE = Depends(RequiresAnyRole({"Study.Write"}))
LIBRARY_WRITE_OR_STUDY_WRITE = Depends(
    RequiresAnyRole({"Library.Write", "Study.Write"})
)
LIBRARY_READ_OR_STUDY_READ = Depends(RequiresAnyRole({"Library.Read", "Study.Read"}))
# Standards import API — ingesting CDISC packages bypasses the library-editability
# and uniqueness guards of the main API, so it gets a role of its own, and that role
# gates the whole app. Reading here is not the broad read `Admin.Read` grants elsewhere:
# it is the review queue and the staged contents of an unimported release, which only
# somebody running an import has any use for.
#
# The two names are kept apart because the routes genuinely differ in what they do, and
# because a narrower read role would then be one line rather than twenty-odd decorators.
LIBRARY_IMPORT_READ = Depends(RequiresAnyRole({"Library.Import"}))
LIBRARY_IMPORT_WRITE = Depends(RequiresAnyRole({"Library.Import"}))
# Feature-flag list is used for UI gating by any authenticated reader
FEATURE_FLAG_READ = Depends(
    RequiresAnyRole({"Admin.Read", "Library.Read", "Study.Read"})
)
ANY = Depends(
    RequiresAnyRole(
        {
            "Library.Write",
            "Study.Write",
            "Library.Read",
            "Study.Read",
            "Admin.Read",
            "Admin.Write",
        }
    )
)
