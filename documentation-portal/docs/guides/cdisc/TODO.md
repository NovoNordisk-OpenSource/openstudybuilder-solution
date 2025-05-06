# Outdated / TODO

TODO review, remove, update or integrate into other parts of the documentation

## Unique Identifiers

> A catalogue is uniquely identified by its name (e.g. 'ADaM CT', 'CDASH CT, 'SDTM CT', ...).

> A codelist is uniquely identified by the concept id that is assigned by CDISC to the codelist.
> However, there is a specialty: two codelists with different concept ids and different names and different submission
> values can refer to the same terms with different submission values. These submission values need to
> be merged into the same term persisting the different submission values as code_ and name_submission_value.

> A term is uniquely identified by the concept id that is assigned by CDISC to the term.

> A package is uniquely identified by the name of the corresponding catalogue plus
the date since when the package is effective according to CDISC.


## Catalogue Priorities

### Attributes Level

If two different catalogues provide different values for the same attributes of the same concept (codelist or term),
then the catalogue with a higher priority according to the following list will overrule the other one:

_1. is the highest priority that overrules all others_
1. SDTM CT
1. ADaM CT
1. CDASH CT
1. SEND CT
1. PRM CT

### Terms Level

> Terms of a codelist will always be combined.

If one of the packages has more terms in a codelist compared to another package,
then all the terms of both packages will be listed under that codelist.
However, it is still tracked which package contained which terms in that codelist
(cf. `(:Package)-[:CONTAINS_TERM]->(:Term)`).


