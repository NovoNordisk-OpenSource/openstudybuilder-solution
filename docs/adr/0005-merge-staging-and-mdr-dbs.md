# Merge staging and mdr databases

## Status

Accepted

## Context

Since the beginning, OpenStudyBuilder has been using 2 separate databases:
* 'cdisc' database which contains only the staging data created by the CDISC Import script
* 'mdr' database which contains everything else (the data needed by the API)

This was fine because only the CDISC CT import script was reading the staging data,
and no API process touched it.

Then a new process for loading in newer CDISCT CT Packages was introduced ; it is API-based
and requires reading and writing staging data. Keeping databases separate would then
mean potential big changes on the DevOps side. For example, the production setup at Novo
was to share the staging database across environments, which would not be possible anymore.

## Decision

Merge the two databases into a single one. Keep the data separate (two "disjointed" graphs),
by adding a new label to the staging data (:CDISCStaging). Make code itself unaware of the
database setup, so OSB Sponsors can keep a two-database setup if they want.

## Consequences

The CT Update process requires going around some core API rules (ability to set a custom date
as start_date for elements ; write to CDISC non-editable Library). Also, merging the two
databases means adding a lot of nodes and relationships to the existing database, so wide db
scans can become much wider.

We introduced protections to avoid logic and data from leaking between "production" OSB and
"staging" level:

* Specific `standards_import` code folder inside `api` module 
* Separate environment variables for db connection between core `api` and `standards_import`
* Forbidding creation of a staging driver session from core `api` repositories
* `lint-imports` contracts to prevent problematic module imports
* Custom `sblint` rules to verify proper usage of `:CDISCStaging` database label
* Option to use custom users with custom roles to segregate MDR & Staging data permissions
