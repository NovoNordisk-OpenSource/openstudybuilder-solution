# Building Blocks

TODO update this section

# Sponsor-specific Adjustments for the Clinical MDR DB

TODO update this section


The following steps are performed by this file:

* Update codelist names
* Update term names
* Flag codelists as parameters

All these steps are done in one single Neo4j transaction.
No batching is taking place at the moment.


[![Image: NN Adjustements](~@source/images/nn/novo-nordisk-adjustments.svg)](../../images/nn/novo-nordisk-adjustments.svg)


### Update codelist names

**High level description:**

Import from file `sponsor_codelist_names.csv`

- Only consider rows where the column
  'Update sponsor preferred name?' = 'Yes'
- Find CTCodelistRoot nodes by the column
  'Codelist concept code'
- Update value from the column
  'Sponsor Preferred Name'

**Additional info:**

The CSV file is read row by row via python (no `LOAD CSV`).

Per row...
* check if an update is needed:
  check if the values in the CSV row differ from what is stored in the db at this point in time
    * if an update is needed, create a new final version: either it is the initial entry or
      a new entry updating a previous entry. In both cases, the entry is set to the `LATEST|LATEST_FINAL` entry.
    * if an update is not needed, don't use the data of that row at all.

This allows to have multiple rows in the CSV file that have the same concept id.
In that case, we will have the last entry of the CSV file in our db as the `LATEST` version.
All previous entries with the same concept id are in the db with previous version numbers
accessible via the `HAS_VERSION` relationship(s).

### Update term names

**High level description:**

Import from file `sponsor_term_names.csv`

- CD_VAL -> CTTermNameValue.name
- CD_VAL_LB -> CTTermNameValue.name_sentence_case

**Additional info:**

The CSV file is read row by row via python (no `LOAD CSV`).

Per row...
* check if an update is needed:
  check if the values in the CSV row differ from what is stored in the db at this point in time
    * if an update is needed, create a new version: either it is the initial entry or
      a new entry updating a previous entry. In both cases, the entry is set to the `LATEST|LATEST_FINAL` entry.
    * if an update is not needed, don't use the data of that row at all.

This allows to have multiple rows in the CSV file that have the same concept id.
In that case, we will have the last entry of the CSV file in our db as the `LATEST` version.
All previous entries with the same concept id are in the db with previous version numbers
accessible via the `HAS_VERSION` relationship(s).

### Flag codelists as parameters

**High level description:**

Import from file `codelist_parameter_names.csv`

- Add the label TemplateParameter to the
  CTCodelistNameValue node
- Add TemplateParameterValueRoot and
  TemplateParameterValue to CTTermNameRoot
  and CTTermNameValue

**Additional info:**

The CSV file is read all at once via python (no `LOAD CSV`).


