import asyncio
import csv
import time

import aiohttp

from .functions.utils import load_env
from .utils.importer import BaseImporter, open_file_async
from .utils.metrics import Metrics

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
API_BASE_URL = load_env("API_BASE_URL")
MDR_MIGRATION_RESPONSE_CODELISTS = load_env("MDR_MIGRATION_RESPONSE_CODELISTS")

CODELIST_TYPE = "Response"


class ResponseCodelists(BaseImporter):
    logging_name = "response_codelists"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)

    async def _new_version_patch_approve_names(
        self, codelist_id: str, body: dict, session: aiohttp.ClientSession
    ):
        """Create new version of codelist names, patch, and approve."""
        versions_path = f"/ct/codelists/{codelist_id}/names/versions"
        patch_path = f"/ct/codelists/{codelist_id}/names"
        approve_path = f"/ct/codelists/{codelist_id}/names/approvals"

        status, result = await self.api.new_version_to_api_async(
            path=versions_path, session=session
        )
        if not 200 <= status < 300:
            self.log.error(
                f"Failed to create new names version for codelist '{codelist_id}': {result}"
            )
            self.metrics.icrement("/ct/codelists/-NamesVersionError")
            return False

        status, result = await self.api.patch_to_api_async(
            path=patch_path, body=body, session=session
        )
        if not 200 <= status < 300:
            self.log.error(
                f"Failed to patch names for codelist '{codelist_id}': {result}"
            )
            self.metrics.icrement("/ct/codelists/-NamesPatchError")
            return False

        time.sleep(0.05)
        status, result = await self.api.approve_async(approve_path, session=session)
        if status != 201:
            self.log.error(
                f"Failed to approve names for codelist '{codelist_id}': {result}"
            )
            self.metrics.icrement("/ct/codelists/-NamesApproveError")
            return False

        self.metrics.icrement("/ct/codelists/-NamesApprove")
        return True

    async def _process_codelist(
        self,
        library_name: str,
        concept_id: str,
        submission_value: str,
        session: aiohttp.ClientSession,
    ):
        """Look up codelist, create new names version, set type to Response, approve."""
        if library_name == "CDISC":
            codelist_id = concept_id
        else:
            # Sponsor — look up by submission value
            codelist_id = self.api.get_codelist_uid(submission_value)
            if not codelist_id:
                self.log.error(
                    f"Could not find Sponsor codelist with submission_value '{submission_value}'"
                )
                return

        label = concept_id or submission_value

        # Check if codelist_type is already set correctly
        names_path = f"/ct/codelists/{codelist_id}/names"
        async with session.get(
            f"{API_BASE_URL}{names_path}", headers=self.api.api_headers
        ) as response:
            if response.ok:
                existing = await response.json()
                if existing.get("codelist_type") == CODELIST_TYPE:
                    self.log.info(
                        f"Codelist '{label}' already has type '{CODELIST_TYPE}', skipping"
                    )
                    self.metrics.icrement("/ct/codelists/-AlreadyResponse")
                    return
            else:
                self.log.error(
                    f"Failed to fetch names for codelist '{label}' (id={codelist_id}), status: {response.status}"
                )
                return

        self.log.info(
            f"Setting codelist_type to '{CODELIST_TYPE}' for '{label}' (id={codelist_id})"
        )

        body = {
            "codelist_type": CODELIST_TYPE,
            "change_description": "Setting codelist type to Response",
        }
        await self._new_version_patch_approve_names(codelist_id, body, session)

    @open_file_async()
    async def handle_response_codelists(self, csvfile, session):
        rows = list(csv.DictReader(csvfile, delimiter=","))

        api_tasks = []
        for row in rows:
            if row.get("is_categoric_response_codelist", "").upper() != "TRUE":
                continue

            library_name = row.get("library_name", "").strip()
            concept_id = row.get("concept_id", "").strip()
            submission_value = row.get("submission_value", "").strip()

            if library_name == "CDISC" and not concept_id:
                self.log.warning(f"CDISC row missing concept_id, skipping: {row}")
                continue
            if library_name != "CDISC" and not submission_value:
                self.log.warning(
                    f"Sponsor row missing submission_value, skipping: {row}"
                )
                continue

            api_tasks.append(
                self._process_codelist(
                    library_name=library_name,
                    concept_id=concept_id,
                    submission_value=submission_value,
                    session=session,
                )
            )

        await asyncio.gather(*api_tasks)

    async def async_run(self):
        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.handle_response_codelists(
                MDR_MIGRATION_RESPONSE_CODELISTS, session
            )

    def run(self):
        self.log.info("Importing response codelists")
        asyncio.run(self.async_run())
        self.log.info("Done importing response codelists")


def main():
    metr = Metrics()
    migrator = ResponseCodelists(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
