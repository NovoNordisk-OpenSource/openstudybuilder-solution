import asyncio
import csv
import os
import re
from datetime import datetime
from urllib.parse import urlparse

import aiohttp

from importers.functions.caselessdict import CaselessDict
from importers.functions.utils import load_env
from importers.utils.importer import BaseImporter
from importers.utils.metrics import Metrics

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
MDR_MIGRATION_NONSTANDARD_VARIABLES_DIRECTORY = load_env(
    "MDR_MIGRATION_NONSTANDARD_VARIABLES_DIRECTORY"
)
MDR_MIGRATION_NONSTANDARD_VARIABLES_FILES = load_env(
    "MDR_MIGRATION_NONSTANDARD_VARIABLES_FILES"
)
MDR_MIGRATION_NONSTANDARD_VARIABLES_LIBRARY = load_env(
    "MDR_MIGRATION_NONSTANDARD_VARIABLES_LIBRARY", default="Sponsor"
)
MDR_MIGRATION_NONSTANDARD_VARIABLES_AIC_FALLBACK = load_env(
    "MDR_MIGRATION_NONSTANDARD_VARIABLES_AIC_FALLBACK", default="SubjectObservation"
)
MDR_MIGRATION_NONSTANDARD_VARIABLES_DEFAULT_LENGTH_CHAR = int(
    load_env("MDR_MIGRATION_NONSTANDARD_VARIABLES_DEFAULT_LENGTH_CHAR", default="200")
)
MDR_MIGRATION_NONSTANDARD_VARIABLES_DEFAULT_LENGTH_NUM = int(
    load_env("MDR_MIGRATION_NONSTANDARD_VARIABLES_DEFAULT_LENGTH_NUM", default="8")
)
MDR_MIGRATION_NONSTANDARD_VARIABLES_AUTO_APPROVE = (
    load_env("MDR_MIGRATION_NONSTANDARD_VARIABLES_AUTO_APPROVE", default="True")
    == "True"
)
MDR_MIGRATION_NONSTANDARD_VARIABLES_WRITE_LOGFILE = (
    load_env("MDR_MIGRATION_NONSTANDARD_VARIABLES_WRITE_LOGFILE", default="False")
    == "True"
)

ROLE_CODELIST_SUBMVAL = "ROLE"
# Non-standard variables create activity-item-classes, so their data type must
# come from the "Semantic Data Type" codelist (SEMTCDT) - the curated subset of
# DATATYPE meant for activity item class definitions - not the generic DATATYPE
# codelist itself, which also contains base/XML terms (e.g. "string", "date")
# that sit above the semantic ones in the specialization hierarchy and aren't
# valid semantic data type choices.
SEMANTIC_DATA_TYPE_CODELIST_SUBMVAL = "SEMTCDT"
# CDISC sometimes prefixes Role values with "Non-Standard " for NSVs, but the
# Role codelist terms themselves don't carry the prefix. Strip it before lookup.
ROLE_PREFIX = "Non-Standard "
ACTIVITY_INSTANCE_CLASSES_PATH = "/activity-instance-classes"
ACTIVITY_ITEM_CLASSES_PATH = "/activity-item-classes"

# The codelist_reference column in the CDISC NSV registry contains free-form
# text that is only trustworthy when it embeds an NCI EVS URL. Source values
# are often wrapped in HTML anchor markup, e.g.
#   (<a href="http://evs.nci.nih.gov/ftp1/CDISC/SDTM/SDTM%20Terminology.html#CL.C66742.NY">NY</a>)
# The concept ID lives in the URL fragment in the form `CL.<code>.<submval>`.
# Any value not matching this host is ignored.
NCI_EVS_HOST = "evs.nci.nih.gov"
NCI_CONCEPT_CODE_RE = re.compile(r"C\d+")
HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.IGNORECASE)

# CDISC AIC names in the NSV registry don't always match the names stored in the
# local DB. Translate before lookup; unmapped names pass through unchanged.
AIC_NAME_MAP: dict[str, str] = {
    "Findings": "Finding",
    "Events": "Event",
    "Interventions": "Intervention",
    "Special Purpose": "SpecialPurpose",
    "Events Interventions": "SubjectObservation",
}

# Source-file formats supported by this importer. Detected per-file from the
# CSV header.
FORMAT_CDISC = "cdisc"
FORMAT_MMA = "mma"
# OSB: exports produced by the OpenStudyBuilder UI's NSV listing — round-trip
# format whose column names use the API's dotted paths (e.g. `non_standard_variable.code`).
FORMAT_OSB = "osb"

# The CDISC NSV registry's xml_datatype and the OSB round-trip's data_type.name
# carry XML/base datatype vocabulary (e.g. "string"), not the Semantic Data Type
# (SEMTCDT) codelist's terms. Most values coincide (e.g. "float", "datetime"),
# but base types with a more specific semantic specialization need translating -
# "string" has no SEMTCDT term of its own; its semantic form is "text", and
# "duration" is represented by the "durationDatetime" term. Values not listed
# here are passed through unchanged.
CDISC_DATA_TYPE_MAP: dict[str, str] = {
    "string": "text",
    "duration": "durationDatetime",
}

# MMA files have no Role column; assign this default for every row.
MMA_DEFAULT_ROLE = "Record Qualifier"
# MMA's data-type vocabulary doesn't match the DATATYPE codelist's term names.
MMA_DATA_TYPE_MAP: dict[str, str] = {
    "text": "Text",
    "integer": "Integer",
    "float": "Float",
    "datetime": "Date Time",
    "durationDatetime": "Duration Date Time",
}

# MMA's sdtm_qnam_qorig value → (Origin Type term name, Origin Source term name).
# Used to populate non_standard_variable.origin_type / .origin_source.
MMA_QORIG_MAP: dict[str, tuple[str, str]] = {
    "Assigned": ("Assigned Value", "Clinical Study Sponsor"),
    "CRF": ("Collected Value", "Investigator"),
    "Derived": ("Derived Value", "Clinical Study Sponsor"),
    "eDT": ("Collected Value", "Vendor"),
}

ORIGIN_TYPE_CODELIST_NAME = "Origin Type"
ORIGIN_SOURCE_CODELIST_NAME = "Origin Source"


class NonStandardVariables(BaseImporter):
    logging_name = "nonstandard_variables"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)
        self.logfile_name = (
            f"nonstandard_variables_import_issues_"
            f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            if MDR_MIGRATION_NONSTANDARD_VARIABLES_WRITE_LOGFILE
            else None
        )

        # Lookups, populated lazily in async_run().
        # Term lookups are keyed by both `name.sponsor_preferred_name` and
        # `submission_value` (CaselessDict) so callers can resolve a term from
        # either form found in source files.
        self.role_terms: CaselessDict = CaselessDict()
        self.data_type_terms: CaselessDict = CaselessDict()
        self.codelist_uids: CaselessDict = CaselessDict()
        # Set of known codelist UIDs, used to validate NCI concept IDs parsed
        # from the codelist_reference URLs in source files.
        self.known_codelist_uids: set[str] = set()
        self.aic_uids: dict[str, str] = {}
        self.aic_fallback_uid: str | None = None
        # Origin Type / Origin Source codelists, used to populate
        # non_standard_variable.origin_type and .origin_source. The codelist
        # UIDs are kept alongside the term lookups because each CTTermRef
        # payload requires both a term_uid and a codelist_uid.
        self.origin_type_terms: CaselessDict = CaselessDict()
        self.origin_type_codelist_uid: str | None = None
        self.origin_source_terms: CaselessDict = CaselessDict()
        self.origin_source_codelist_uid: str | None = None

    # ---------------------------------------------------------------
    # Lookups
    # ---------------------------------------------------------------
    def _build_term_lookup(self, codelist_uid: str) -> CaselessDict:
        """Map a codelist's terms to their UID, keyed by every recognisable form
        a source file might use: sponsor_preferred_name, nci_preferred_name and
        submission_value. Case-insensitive. The /ct/codelists/{uid}/terms
        endpoint returns these as top-level fields (CTCodelistTerm)."""
        terms = self.api.get_all_from_api(f"/ct/codelists/{codelist_uid}/terms")
        lookup: CaselessDict = CaselessDict()
        if not terms:
            return lookup
        for term in terms:
            term_uid = term.get("term_uid")
            if not term_uid:
                continue
            for key in (
                term.get("sponsor_preferred_name"),
                term.get("nci_preferred_name"),
                term.get("submission_value"),
            ):
                if key and key not in lookup:
                    lookup[key] = term_uid
        return lookup

    def _load_lookups(self):
        all_codelist_uids = self.api.get_codelists_uid_and_submval()
        self.codelist_uids = all_codelist_uids
        self.known_codelist_uids = {
            uid.upper() for uid in self.codelist_uids.values() if uid
        }

        role_codelist_uid = all_codelist_uids.get(ROLE_CODELIST_SUBMVAL)
        if role_codelist_uid:
            self.role_terms = self._build_term_lookup(role_codelist_uid)
        else:
            self.log.error(
                "Codelist '%s' (Role) not found - role_uid lookups will fail",
                ROLE_CODELIST_SUBMVAL,
            )

        data_type_codelist_uid = all_codelist_uids.get(
            SEMANTIC_DATA_TYPE_CODELIST_SUBMVAL
        )
        if data_type_codelist_uid:
            self.data_type_terms = self._build_term_lookup(data_type_codelist_uid)
        else:
            self.log.error(
                "Codelist '%s' (Semantic Data Type) not found - data_type_uid "
                "lookups will fail",
                SEMANTIC_DATA_TYPE_CODELIST_SUBMVAL,
            )

        self.aic_uids = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_INSTANCE_CLASSES_PATH),
            identifier="name",
            value="uid",
        )
        self.aic_fallback_uid = self.aic_uids.get(
            MDR_MIGRATION_NONSTANDARD_VARIABLES_AIC_FALLBACK
        )
        if not self.aic_fallback_uid:
            self.log.warning(
                "Fallback Activity Instance Class '%s' not found - rows with no "
                "matching class will be skipped",
                MDR_MIGRATION_NONSTANDARD_VARIABLES_AIC_FALLBACK,
            )

        codelist_uids_by_name = self.api.get_code_lists_uids()
        self.origin_type_codelist_uid = codelist_uids_by_name.get(
            ORIGIN_TYPE_CODELIST_NAME
        )
        if self.origin_type_codelist_uid:
            self.origin_type_terms = self._build_term_lookup(
                self.origin_type_codelist_uid
            )
        else:
            self.log.warning(
                "Codelist '%s' not found - origin_type will be omitted from MMA rows",
                ORIGIN_TYPE_CODELIST_NAME,
            )
        self.origin_source_codelist_uid = codelist_uids_by_name.get(
            ORIGIN_SOURCE_CODELIST_NAME
        )
        if self.origin_source_codelist_uid:
            self.origin_source_terms = self._build_term_lookup(
                self.origin_source_codelist_uid
            )
        else:
            self.log.warning(
                "Codelist '%s' not found - origin_source will be omitted from MMA rows",
                ORIGIN_SOURCE_CODELIST_NAME,
            )

    # ---------------------------------------------------------------
    # Row → payload
    # ---------------------------------------------------------------
    def _slugify_name(self, label: str) -> str:
        return label.strip().lower().replace(" ", "_")

    def _resolve_aics(self, class_cell: str) -> list[dict]:
        names = (
            [n.strip() for n in class_cell.split(",") if n.strip()]
            if class_cell
            else []
        )
        uids: list[str] = []
        for name in names:
            local_name = AIC_NAME_MAP.get(name, name)
            uid = self.aic_uids.get(local_name)
            if uid is None:
                self.log.warning(
                    "Activity Instance Class '%s' (mapped to '%s') not found, "
                    "ignoring (row may fall back to '%s')",
                    name,
                    local_name,
                    MDR_MIGRATION_NONSTANDARD_VARIABLES_AIC_FALLBACK,
                )
            else:
                uids.append(uid)
        if not uids and self.aic_fallback_uid:
            uids.append(self.aic_fallback_uid)
        return [
            {
                "uid": uid,
                "mandatory": False,
                "is_adam_param_specific_enabled": False,
                "is_additional_optional": False,
                "is_default_linked": False,
            }
            for uid in uids
        ]

    def _default_length(self, simple_datatype: str) -> int:
        if (simple_datatype or "").strip().lower().startswith("num"):
            return MDR_MIGRATION_NONSTANDARD_VARIABLES_DEFAULT_LENGTH_NUM
        return MDR_MIGRATION_NONSTANDARD_VARIABLES_DEFAULT_LENGTH_CHAR

    def _extract_nci_concept_id(self, value: str) -> str | None:
        """Return the NCI EVS codelist concept ID embedded in `value`, or None.

        Only http/https URLs whose host is `evs.nci.nih.gov` are considered
        valid. The value may be a bare URL or an HTML anchor tag wrapping one;
        the concept ID lives in the URL fragment for CDISC's SDTM Terminology
        links (e.g. `#CL.C66742.NY`), with query/path as fallbacks.
        """
        value = (value or "").strip()
        if not value:
            return None
        href_match = HREF_RE.search(value)
        url = href_match.group(1) if href_match else value
        try:
            parsed = urlparse(url)
        except ValueError:
            return None
        if parsed.scheme.lower() not in ("http", "https"):
            return None
        if (parsed.hostname or "").lower() != NCI_EVS_HOST:
            return None
        for haystack in (parsed.fragment, parsed.query, parsed.path):
            if not haystack:
                continue
            match = NCI_CONCEPT_CODE_RE.search(haystack)
            if match:
                return match.group(0)
        return None

    def _resolve_codelist_url(self, codelist_reference: str) -> list[str]:
        """CDISC format: codelist_reference is an NCI EVS URL (or HTML anchor
        wrapping one). Return the parsed concept ID if it matches a known
        codelist UID."""
        if not codelist_reference:
            return []
        concept_id = self._extract_nci_concept_id(codelist_reference)
        if not concept_id:
            self.log.warning(
                "Ignoring codelist_reference '%s' - not a valid NCI EVS URL",
                codelist_reference,
            )
            return []
        if concept_id not in self.known_codelist_uids:
            self.log.warning(
                "NCI concept ID '%s' (from '%s') does not match any known "
                "codelist UID - omitting from valid_codelist_uids",
                concept_id,
                codelist_reference,
            )
            return []
        return [concept_id]

    def _resolve_mma_origin(
        self, qorig: str, variable_name: str
    ) -> tuple[dict | None, dict | None]:
        """Translate an MMA `sdtm_qnam_qorig` value into CTTermRef payloads for
        non_standard_variable.origin_type and .origin_source. Unknown values
        return (None, None) with a warning; missing terms also return None
        for that side only."""
        qorig = (qorig or "").strip()
        if not qorig:
            return None, None
        mapping = MMA_QORIG_MAP.get(qorig)
        if mapping is None:
            self.log.warning(
                "Unknown qorig '%s' for variable '%s' - no origin mapping applied",
                qorig,
                variable_name,
            )
            return None, None
        type_name, source_name = mapping

        origin_type_ref: dict | None = None
        type_uid = self.origin_type_terms.get(type_name)
        if type_uid and self.origin_type_codelist_uid:
            origin_type_ref = {
                "term_uid": type_uid,
                "codelist_uid": self.origin_type_codelist_uid,
            }
        else:
            self.log.warning(
                "Origin Type '%s' not found for variable '%s' - omitting",
                type_name,
                variable_name,
            )

        origin_source_ref: dict | None = None
        source_uid = self.origin_source_terms.get(source_name)
        if source_uid and self.origin_source_codelist_uid:
            origin_source_ref = {
                "term_uid": source_uid,
                "codelist_uid": self.origin_source_codelist_uid,
            }
        else:
            self.log.warning(
                "Origin Source '%s' not found for variable '%s' - omitting",
                source_name,
                variable_name,
            )

        return origin_type_ref, origin_source_ref

    def _resolve_codelist_submval(self, submission_value: str) -> list[str]:
        """MMA format: sdtm_qnam_ct is a bare codelist submission value."""
        submission_value = (submission_value or "").strip()
        if not submission_value:
            return []
        uid = self.codelist_uids.get(submission_value)
        if not uid:
            self.log.warning(
                "Codelist submission value '%s' not found - omitting from "
                "valid_codelist_uids",
                submission_value,
            )
            return []
        return [uid]

    # ---------------------------------------------------------------
    # Per-format row adapters
    #
    # Each adapter returns a "canonical" dict consumed by _build_payload.
    # Required keys: variable_name, label, definition, role_input,
    # data_type_input, length, valid_codelist_uids, activity_instance_classes,
    # is_multiple, is_cdisc_defined.
    # Optional keys (None when absent): algorithm, derivation_rule, origin_type,
    # origin_source, name_override, nci_concept_id, nci_concept_name.
    # ---------------------------------------------------------------
    def _canonicalize_cdisc(self, row: dict) -> dict | None:
        variable_name = (row.get("variable_name") or "").strip()
        label = (row.get("label") or "").strip()
        if not variable_name or not label:
            self.log.warning(
                "Skipping CDISC row with missing variable_name or label: %s", row
            )
            return None

        role_value = (row.get("role") or "").strip()
        if role_value.startswith(ROLE_PREFIX):
            role_value = role_value[len(ROLE_PREFIX) :].strip()

        length_cell = (row.get("length") or "").strip()
        simple_datatype = row.get("simple_datatype") or ""
        try:
            length = (
                int(length_cell)
                if length_cell
                else self._default_length(simple_datatype)
            )
        except ValueError:
            length = self._default_length(simple_datatype)

        raw_data_type = (row.get("xml_datatype") or "").strip()
        data_type_input = CDISC_DATA_TYPE_MAP.get(raw_data_type, raw_data_type)

        return {
            "variable_name": variable_name,
            "label": label,
            "definition": (row.get("description_and_notes") or "").strip() or None,
            "role_input": role_value,
            "data_type_input": data_type_input,
            "length": length,
            "valid_codelist_uids": self._resolve_codelist_url(
                row.get("codelist_reference") or ""
            ),
            "activity_instance_classes": self._resolve_aics(
                row.get("limited_to_classes") or ""
            ),
            "is_multiple": False,
            "is_cdisc_defined": True,
            "algorithm": None,
            "origin_type": None,
            "origin_source": None,
        }

    def _canonicalize_mma(self, row: dict) -> dict | None:
        if (row.get("cd_list_val_status") or "").strip().upper() != "A":
            return None
        variable_name = (row.get("cd_val") or "").strip()
        label = (row.get("cd_val_lb") or "").strip()
        if not variable_name or not label:
            self.log.warning(
                "Skipping MMA row with missing cd_val or cd_val_lb: %s", row
            )
            return None

        raw_data_type = (row.get("sdtm_qnam_data_type") or "").strip()
        data_type_input = MMA_DATA_TYPE_MAP.get(raw_data_type, raw_data_type)

        length_cell = (row.get("sdtm_qnam_length") or "").strip()
        try:
            length = (
                int(length_cell)
                if length_cell
                else self._default_length(
                    "Num" if raw_data_type in ("integer", "float") else "Char"
                )
            )
        except ValueError:
            length = self._default_length(
                "Num" if raw_data_type in ("integer", "float") else "Char"
            )

        origin_type_ref, origin_source_ref = self._resolve_mma_origin(
            row.get("sdtm_qnam_qorig") or "", variable_name
        )

        return {
            "variable_name": variable_name,
            "label": label,
            "definition": (row.get("cd_val_desc") or "").strip() or None,
            "role_input": MMA_DEFAULT_ROLE,
            "data_type_input": data_type_input,
            "length": length,
            "valid_codelist_uids": self._resolve_codelist_submval(
                row.get("sdtm_qnam_ct") or ""
            ),
            "activity_instance_classes": self._resolve_aics(""),
            "is_multiple": (row.get("sdtm_qnam_multiple") or "").strip().upper() == "Y",
            "is_cdisc_defined": False,
            "algorithm": (row.get("sdtm_qnam_algorithm") or "").strip() or None,
            "origin_type": origin_type_ref,
            "origin_source": origin_source_ref,
        }

    def _resolve_origin_term(
        self,
        term_name: str,
        terms: CaselessDict,
        codelist_uid: str | None,
        codelist_label: str,
        variable_name: str,
    ) -> dict | None:
        """Look up an Origin Type / Origin Source CTTermRef by direct term name
        (as it appears in OSB exports). Returns None for empty input or unknown
        terms (with a warning in the latter case)."""
        term_name = (term_name or "").strip()
        if not term_name:
            return None
        uid = terms.get(term_name)
        if uid and codelist_uid:
            return {"term_uid": uid, "codelist_uid": codelist_uid}
        self.log.warning(
            "%s '%s' not found for variable '%s' - omitting",
            codelist_label,
            term_name,
            variable_name,
        )
        return None

    def _canonicalize_osb(self, row: dict) -> dict | None:
        variable_name = (row.get("non_standard_variable.code") or "").strip()
        label = (row.get("display_name") or "").strip()
        if not variable_name or not label:
            self.log.warning(
                "Skipping OSB row with missing non_standard_variable.code or "
                "display_name: %s",
                row,
            )
            return None

        raw_data_type = (row.get("data_type.name") or "").strip()
        data_type_input = CDISC_DATA_TYPE_MAP.get(raw_data_type, raw_data_type)
        length_cell = (row.get("non_standard_variable.length") or "").strip()
        try:
            length = (
                int(length_cell)
                if length_cell
                else self._default_length(data_type_input)
            )
        except ValueError:
            length = self._default_length(data_type_input)

        return {
            "variable_name": variable_name,
            "label": label,
            "name_override": (row.get("name") or "").strip() or None,
            "definition": (row.get("definition") or "").strip() or None,
            "role_input": (row.get("role.name") or "").strip(),
            "data_type_input": data_type_input,
            "length": length,
            "valid_codelist_uids": [],
            "activity_instance_classes": self._resolve_aics(
                row.get("activity_instance_classes.name") or ""
            ),
            "is_multiple": (row.get("non_standard_variable.is_multiple") or "")
            .strip()
            .lower()
            == "true",
            # OSB exports don't carry the is_cdisc_defined flag; assume sponsor
            # (False) since round-tripped rows are typically user-edited.
            "is_cdisc_defined": False,
            "algorithm": (row.get("non_standard_variable.algorithm") or "").strip()
            or None,
            "derivation_rule": (
                row.get("non_standard_variable.derivation_rule") or ""
            ).strip()
            or None,
            "nci_concept_id": (row.get("nci_concept_id") or "").strip() or None,
            "nci_concept_name": (row.get("nci_concept_name") or "").strip() or None,
            "origin_type": self._resolve_origin_term(
                row.get("non_standard_variable.origin_type.name") or "",
                self.origin_type_terms,
                self.origin_type_codelist_uid,
                ORIGIN_TYPE_CODELIST_NAME,
                variable_name,
            ),
            "origin_source": self._resolve_origin_term(
                row.get("non_standard_variable.origin_source.name") or "",
                self.origin_source_terms,
                self.origin_source_codelist_uid,
                ORIGIN_SOURCE_CODELIST_NAME,
                variable_name,
            ),
        }

    def _build_payload(self, canonical: dict, order: int) -> dict | None:
        variable_name = canonical["variable_name"]
        label = canonical["label"]

        role_uid = self.role_terms.get(canonical["role_input"])
        if not role_uid:
            self.log.warning(
                "Role '%s' not found for variable '%s' - skipping",
                canonical["role_input"],
                variable_name,
            )
            return None

        data_type_uid = self.data_type_terms.get(canonical["data_type_input"])
        if not data_type_uid:
            self.log.warning(
                "Data Type '%s' not found for variable '%s' - skipping",
                canonical["data_type_input"],
                variable_name,
            )
            return None

        aics = canonical["activity_instance_classes"]
        if not aics:
            self.log.warning(
                "No Activity Instance Class resolved for variable '%s' and no "
                "fallback available - skipping",
                variable_name,
            )
            return None

        nsv: dict = {
            "code": variable_name,
            "is_multiple": canonical["is_multiple"],
            "length": canonical["length"],
            "is_cdisc_defined": canonical["is_cdisc_defined"],
        }
        if canonical.get("algorithm"):
            nsv["algorithm"] = canonical["algorithm"]
        if canonical.get("derivation_rule"):
            nsv["derivation_rule"] = canonical["derivation_rule"]
        if canonical.get("origin_type"):
            nsv["origin_type"] = canonical["origin_type"]
        if canonical.get("origin_source"):
            nsv["origin_source"] = canonical["origin_source"]

        body = {
            "name": canonical.get("name_override") or self._slugify_name(label),
            "display_name": label,
            "order": order,
            "library_name": MDR_MIGRATION_NONSTANDARD_VARIABLES_LIBRARY,
            "role_uid": role_uid,
            "data_type_uid": data_type_uid,
            "activity_instance_classes": aics,
            "definition": canonical["definition"],
            "non_standard_variable": nsv,
        }
        if canonical.get("nci_concept_id"):
            body["nci_concept_id"] = canonical["nci_concept_id"]
        if canonical.get("nci_concept_name"):
            body["nci_concept_name"] = canonical["nci_concept_name"]
        if canonical["valid_codelist_uids"]:
            body["valid_codelist_uids"] = canonical["valid_codelist_uids"]
        return body

    # ---------------------------------------------------------------
    # File handling
    # ---------------------------------------------------------------
    def _detect_format(self, header_line: str) -> str | None:
        """Identify the source-file format from the CSV header.

        CDISC files are comma-delimited and have `variable_name` / `xml_datatype`
        columns. MMA files are pipe-delimited and start with `cd_list_id` / `cd_val`.
        OSB files are comma-delimited round-trip exports from the OpenStudyBuilder
        UI and are recognised by the dotted-path header `non_standard_variable.code`.
        """
        if "cd_val" in header_line and "cd_list_id" in header_line:
            return FORMAT_MMA
        if "non_standard_variable.code" in header_line:
            return FORMAT_OSB
        if "variable_name" in header_line:
            return FORMAT_CDISC
        return None

    async def _import_file(self, path: str, session: aiohttp.ClientSession):
        if not path:
            self.log.info("Empty filename, skipping")
            return
        self.log.info("Opening file: %s", path)
        try:
            with open(path, encoding="utf-8-sig") as csvfile:
                first_line = csvfile.readline()
                fmt = self._detect_format(first_line)
                if fmt is None:
                    self.log.error(
                        "Unrecognised CSV format for %s (header: %s)",
                        path,
                        first_line.rstrip()[:200],
                    )
                    return
                csvfile.seek(0)
                delimiter = "|" if fmt == FORMAT_MMA else ","
                rows = list(csv.DictReader(csvfile, delimiter=delimiter))
        except FileNotFoundError:
            self.log.error("File %s not found, skipping", path)
            return

        self.log.info("Detected '%s' format with %d rows in %s", fmt, len(rows), path)
        canonicalizer = {
            FORMAT_MMA: self._canonicalize_mma,
            FORMAT_OSB: self._canonicalize_osb,
            FORMAT_CDISC: self._canonicalize_cdisc,
        }[fmt]

        post_tasks = []
        bodies: list[dict] = []
        total_rows = 0
        for index, row in enumerate(rows, start=1):
            total_rows += 1
            canonical = canonicalizer(row)
            if canonical is None:
                continue
            body = self._build_payload(canonical, order=index)
            if body is None:
                continue
            bodies.append(body)
            post_tasks.append(
                self.api.post_to_api_async(
                    url=ACTIVITY_ITEM_CLASSES_PATH,
                    body=body,
                    session=session,
                    logfile_name=self.logfile_name,
                )
            )

        self.log.info(
            "Posting %d non-standard variables (%d rows skipped during payload build)",
            len(post_tasks),
            total_rows - len(post_tasks),
        )
        results = await asyncio.gather(*post_tasks)

        created = 0
        failed = 0
        for body, (status, result) in zip(bodies, results):
            if status in (200, 201) and isinstance(result, dict):
                created += 1
                continue
            failed += 1
            detail = (
                result.get("message") or result.get("detail")
                if isinstance(result, dict)
                else result
            )
            self.log.warning(
                "POST %s failed for variable '%s' (status %s): %s",
                ACTIVITY_ITEM_CLASSES_PATH,
                body["non_standard_variable"]["code"],
                status,
                detail,
            )

        self.log.info(
            "Non-standard variables created: %d, failed: %d, skipped: %d (total rows: %d)",
            created,
            failed,
            total_rows - len(post_tasks),
            total_rows,
        )

        if not MDR_MIGRATION_NONSTANDARD_VARIABLES_AUTO_APPROVE:
            return

        approve_tasks = []
        for body, (status, result) in zip(bodies, results):
            if status not in (200, 201) or not isinstance(result, dict):
                continue
            uid = result.get("uid")
            if not uid:
                self.log.warning(
                    "No uid returned for variable '%s' - cannot approve",
                    body["non_standard_variable"]["code"],
                )
                continue
            approve_tasks.append(
                self.api.approve_async(
                    f"{ACTIVITY_ITEM_CLASSES_PATH}/{uid}/approvals", session=session
                )
            )
        if approve_tasks:
            self.log.info("Approving %d non-standard variables", len(approve_tasks))
            await asyncio.gather(*approve_tasks)

    async def async_run(self):
        self._load_lookups()
        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            for filename in (
                f.strip()
                for f in MDR_MIGRATION_NONSTANDARD_VARIABLES_FILES.split(",")
                if f.strip()
            ):
                path = os.path.join(
                    MDR_MIGRATION_NONSTANDARD_VARIABLES_DIRECTORY, filename
                )
                await self._import_file(path, session)

    def run(self):
        self.log.info("Importing non-standard variables")
        if self.logfile_name:
            with open(self.logfile_name, "w") as f:
                f.write("Non-Standard Variables Import Issues\n")
        asyncio.run(self.async_run())
        self.log.info("Done importing non-standard variables")


def main():
    metr = Metrics()
    migrator = NonStandardVariables(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
