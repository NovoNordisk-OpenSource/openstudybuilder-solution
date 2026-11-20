# Allow literal square brackets in syntax template names

## Status

Accepted

## Context

Syntax templates (objective, endpoint, timeframe, criteria, footnote and
activity instruction templates) mark placeholders as `[Parameter name]`. When
an instance is created, each placeholder is filled with a template parameter
value.

The name was validated strictly before being accepted: brackets had to be
balanced and non-nested, and every bracketed span had to be an existing
template parameter. As a result, a template could not contain bracketed text
that is not a placeholder, such as `[see note]`.

## Decision

A bracketed span `[Name]` is a placeholder only if `Name` is a template
parameter. All other bracketed text is literal, including unknown names,
unbalanced brackets and empty brackets. In nested brackets such as
`[a [Activity] b]`, only the innermost span can be a placeholder.

- **Placeholders are resolved against different parameter sets.** A template
  being created or edited as a draft (version below 1.0) is resolved against
  all existing template parameters. A template loaded from the database is
  resolved only against the parameters it is linked to (`USES_PARAMETER`,
  `USES_VALUE` for timeframe templates). Creating a template parameter later
  therefore cannot turn literal text in a stored template into a placeholder.
- **Approved templates keep their literal text.** `edit_draft` and
  `create_new_version` keep bracketed text that is literal in the current
  version literal, even if a parameter with that name has been created since.
  Both then reject any change to the number or order of parameters.
  `create_new_version` did not have this check before.
- **Literal brackets are escaped in instance names** as `&#91;` and `&#93;`
  (`escape_literal_brackets`), so the only raw brackets left in an instance
  name are filled placeholders. `convert_to_plain` removes raw brackets before
  stripping HTML, so the escaped ones survive.
- **The frontend applies the same rule.** `splitTemplate` in
  `templateParameters.js` treats a match as a placeholder only if its name is
  in the list of parameter names it is given: all parameter types when
  authoring, the template's own parameters for existing items.
- **Syntax validation was removed.** `is_syntax_of_template_name_correct`, the
  `/pre-validate` endpoints and the "Verify syntax" button are gone. The only
  check left was a non-blank name, which the API already enforces (`InputModel`
  strips whitespace and the create/edit models set `min_length=1`).

## Consequences

- Authors can use ordinary bracketed text in template names.
- The domain layer no longer validates the name at all. A blank name is
  rejected only by the request models.
- Literal text in an approved template stays literal without any warning. A
  draft that was never approved has no stored parameter links, so editing it
  after a matching parameter has been created turns that text into a
  placeholder.
- `create_new_version` now returns a 400 if the parameters change. The only
  frontend caller resubmits the unchanged name, so only direct API calls are
  affected.
- `TemplateVO.parameter_names` is a stored field rather than derived from
  `name`, so code that builds a `TemplateVO` must pass it.
- Any new code that builds an instance name from a template must escape
  literal brackets with `escape_literal_brackets`.
- Calls to the removed `/pre-validate` endpoints now return 404.
