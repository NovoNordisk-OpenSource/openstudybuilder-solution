"""Common query patterns"""

# pylint: disable=invalid-name

from textwrap import dedent

# Gives ct_terms_datetime for effective study_standard_version of a StudyValue
study_standard_version_ct_terms_datetime = dedent("""
    CALL {
        WITH study_value 
        OPTIONAL MATCH (study_value)-[:HAS_STUDY_STANDARD_VERSION]->(study_standard_version:StudyStandardVersion)-[:HAS_CT_PACKAGE]->(ct_package:CTPackage)
        WHERE ct_package.uid CONTAINS "SDTM CT"
        RETURN datetime(toString(date(ct_package.effective_date)) + 'T23:59:59.999999000Z') AS ct_terms_datetime
    }
""")

# Gives CTTermNameValue as {value} for a CTTermRoot {root} at given ct_terms_datetime (f-string)
ct_term_name_at_datetime = dedent("""
    CALL {{
        WITH {root}, ct_terms_datetime
        OPTIONAL MATCH ({root})-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[version:HAS_VERSION]->(value:CTTermNameValue)
        WHERE version.status IN ['Final', 'Retired']
        WITH *, (ct_terms_datetime IS NULL OR version.start_date <= ct_terms_datetime
            AND (version.end_date IS NULL OR version.end_date > ct_terms_datetime)) AS dates_match
        ORDER BY dates_match DESC, version.start_date DESC
        LIMIT 1
        RETURN value {{
            .*,
            uid: {root}.uid,
            term_uid: {root}.uid,
            sponsor_preferred_name: value.name,
            queried_effective_date: CASE WHEN dates_match THEN ct_terms_datetime ELSE null END,
            date_conflict: NOT dates_match
        }} AS {value}
    }}
""").rstrip()

# Shared body for CT term + codelist resolution. Placeholders: {root}, {value}, and
# either context import/carry/codelist_resolve (with CTTermContext) or no-context variants.
#
# date_conflict is true when any resolved name/attributes/codelist version is a fallback
# (not valid at ct_terms_datetime). Missing sides are ignored (coalesce to true).
# queried_effective_date is set only when all resolved sides match the package datetime.
#
# Codelist selection is deterministic: prefer HAS_SELECTED_CODELIST from context when
# present; otherwise the active HAS_TERM link with the lowest codelist_root.uid.
_ct_term_with_codelist_body = """
        OPTIONAL MATCH ({root})-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[name_version:HAS_VERSION]->(name_value:CTTermNameValue)
        WHERE name_version.status IN ['Final', 'Retired']
        WITH {root}, ct_terms_datetime{ctx_carry}, name_version, name_value,
            (ct_terms_datetime IS NULL OR name_version.start_date <= ct_terms_datetime
            AND (name_version.end_date IS NULL OR name_version.end_date > ct_terms_datetime)) AS name_dates_match
        ORDER BY name_dates_match DESC, name_version.start_date DESC
        LIMIT 1
        WITH {root}, ct_terms_datetime{ctx_carry}, name_value, name_dates_match
        OPTIONAL MATCH ({root})-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[attr_version:HAS_VERSION]->(attr_value:CTTermAttributesValue)
        WHERE attr_version.status IN ['Final', 'Retired']
        WITH {root}, ct_terms_datetime{ctx_carry}, name_value, name_dates_match, attr_version, attr_value,
            (ct_terms_datetime IS NULL OR attr_version.start_date <= ct_terms_datetime
            AND (attr_version.end_date IS NULL OR attr_version.end_date > ct_terms_datetime)) AS attr_dates_match
        ORDER BY attr_dates_match DESC, attr_version.start_date DESC
        LIMIT 1
        WITH {root}, ct_terms_datetime{ctx_carry}, name_value, name_dates_match, attr_value, attr_dates_match
{codelist_resolve}
        OPTIONAL MATCH (codelist_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[cl_attr_version:HAS_VERSION]->(cl_attr_value:CTCodelistAttributesValue)
        WHERE codelist_root IS NOT NULL AND cl_attr_version.status IN ['Final', 'Retired']
        WITH {root}, ct_terms_datetime, name_value, name_dates_match, attr_value, attr_dates_match,
            codelist_root, clterm, cl_attr_version, cl_attr_value,
            (ct_terms_datetime IS NULL OR cl_attr_version.start_date <= ct_terms_datetime
            AND (cl_attr_version.end_date IS NULL OR cl_attr_version.end_date > ct_terms_datetime)) AS cl_attr_dates_match
        ORDER BY cl_attr_dates_match DESC, cl_attr_version.start_date DESC
        LIMIT 1
        WITH {root}, ct_terms_datetime, name_value, name_dates_match, attr_value, attr_dates_match,
            codelist_root, clterm, cl_attr_value, cl_attr_dates_match,
            (coalesce(name_dates_match, true)
                AND coalesce(attr_dates_match, true)
                AND coalesce(cl_attr_dates_match, true)) AS dates_ok
        RETURN {{
            term_uid: coalesce({root}.uid, ''),
            sponsor_preferred_name: name_value.name,
            submission_value: clterm.submission_value,
            concept_id: attr_value.concept_id,
            codelist_uid: codelist_root.uid,
            codelist_name: cl_attr_value.name,
            codelist_submission_value: cl_attr_value.submission_value,
            queried_effective_date: CASE WHEN dates_ok THEN ct_terms_datetime ELSE null END,
            date_conflict: NOT dates_ok
        }} AS {value}
"""

_ct_term_codelist_resolve_with_context = """
        // Fallback only triggers when no codelist was selected via context
        // (codelist_root_ctx IS NULL), not when the selected codelist lacks an
        // active HAS_TERM link (clterm_ctx IS NULL). HAS_SELECTED_CODELIST is an
        // explicit study-level choice, not a date-driven fact, so a lapsed term
        // membership should surface as a null submission_value rather than being
        // silently swapped for an unrelated codelist that happens to have one.
        OPTIONAL MATCH ({context_var})-[:HAS_SELECTED_CODELIST]->(codelist_root_ctx:CTCodelistRoot)
        OPTIONAL MATCH (codelist_root_ctx)-[ht_ctx:HAS_TERM]->(clterm_ctx:CTCodelistTerm)-[:HAS_TERM_ROOT]->({root})
        WHERE ht_ctx.end_date IS NULL
        OPTIONAL MATCH (codelist_root_fb:CTCodelistRoot)-[ht_fb:HAS_TERM]->(clterm_fb:CTCodelistTerm)-[:HAS_TERM_ROOT]->({root})
        WHERE ht_fb.end_date IS NULL AND codelist_root_ctx IS NULL
        WITH {root}, ct_terms_datetime, name_value, name_dates_match, attr_value, attr_dates_match,
            coalesce(codelist_root_ctx, codelist_root_fb) AS codelist_root,
            coalesce(clterm_ctx, clterm_fb) AS clterm
        ORDER BY codelist_root.uid ASC
        LIMIT 1
"""

_ct_term_codelist_resolve_no_context = """
        OPTIONAL MATCH (codelist_root:CTCodelistRoot)-[ht:HAS_TERM]->(clterm:CTCodelistTerm)-[:HAS_TERM_ROOT]->({root})
        WHERE ht.end_date IS NULL
        WITH {root}, ct_terms_datetime, name_value, name_dates_match, attr_value, attr_dates_match,
            codelist_root, clterm
        ORDER BY codelist_root.uid ASC
        LIMIT 1
"""


def _ct_term_with_codelist_call(
    *, import_with: str, ctx_carry: str, codelist_resolve: str
) -> str:
    # Build without f-strings so {root}/{value}/{context_var} stay for .format().
    body = _ct_term_with_codelist_body.replace("{ctx_carry}", ctx_carry).replace(
        "{codelist_resolve}", codelist_resolve
    )
    return dedent(
        "\n    CALL {{\n        " + import_with + "\n" + body + "\n    }}\n"
    ).rstrip()


# Gives CT term with codelist metadata as {value} for a CTTermRoot {root} at ct_terms_datetime.
# {context_var} is a CTTermContext variable in scope (no aliasing in CALL import WITH).
ct_term_with_codelist_at_datetime = _ct_term_with_codelist_call(
    import_with="WITH {root}, ct_terms_datetime, {context_var}",
    ctx_carry=", {context_var}",
    codelist_resolve=_ct_term_codelist_resolve_with_context,
)

# Same as above but without CTTermContext (deterministic lowest-uid active HAS_TERM).
ct_term_with_codelist_at_datetime_no_context = _ct_term_with_codelist_call(
    import_with="WITH {root}, ct_terms_datetime",
    ctx_carry="",
    codelist_resolve=_ct_term_codelist_resolve_no_context,
)
