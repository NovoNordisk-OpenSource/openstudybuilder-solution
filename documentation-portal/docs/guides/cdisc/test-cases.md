# Test-Cases

**TODO update**: check if this section is correct and adjust references to test cases.


The following situations can occur while importing the CDISC data
and are considered to be **consistent**/**valid**:

- A catalogue (ADaM, CDASH, SDTM, ..) was added
  - Action: Import as usual.
  - Example:
  > We receive the package 'COA CT 2014-12-19' and we have never imported packages for the 'COA'
  > catalogue before.
  > This is the initial import of that package and catalogue.
  > -> Create the codelists including all terms; create the catalogue and the package.

- A catalogue (ADaM, CDASH, SDTM, ..) was discontinued -> Don't do anything.
  > Example: We have imported the package 'ADaM CT 2020-03-27'. The next time we import from CDISC,
  > we do not receive a package for the ADaM catalogue.
  > -> We don't take any action and leave everything as is.
  > May be the case if codelists are transferred to another catalogue.
  > May be the case if CDISC renames a catalogue.

- One or more codelists were added -> add those codelists to the corresponding catalogue.

  If we have that codelist in the DB already: -> update with the rules below including all terms.
  Check for inconsistencies across all package files.
  Even if the codelist was imported and deactivated before, we will create a new final version and
  therefore re-activate the codelist. In that case, we will also re-activate the Novo Nordisk managed name.

  If we don't have the codelist in the DB: Create the codelist including all terms.
  > Example: We have imported the package 'ADaM CT 2014-09-26'. The next time we import from CDISC,
  > the package 'ADaM CT 2015-12-18' has a new codelist C124296 'Subject Trial Status [SBJTSTAT]' with two terms (C25250 [COMPLETED] and C53279 [ONGOING]).

- One or more attributes of an existing codelist changed: -> Create a new final version (cf. `CTCodelistAttributesValue`).
  If the attribute value was in final version 2.0 then create a new 3.0 version.
  If the attribute value was in retired version 2.0 then create a new 3.0 version.
  Values are not supposed to be in draft version, so that is not applicable.

  > Example: We have imported the package 'ADaM CT 2015-12-18' where the codelist C124296 has the attribute `extensible=false`.
  > In the next package 'ADaM CT 2016-03-25' the attribute of C124296 changed to be `extensible=true`.
  > -> Create a new final version of the `CTCodelistAttributesValue` node with the updated property (`extensible=true`).
  > (Note here that in this example, the C124296 Codelist is having a new Term in the 'ADaM CT 2016-03-25' package - See Term C25484 [DISCONTINUED])
  QUESTION: DO WE NEED HERE A WAY TO ORDER THE TERM INSIDE A CODELIST??? Based on the example above, we can see that this added term is between the two existing one...

- One or more codelists were removed -> retire the removed codelists including the `CTCodelistAttributesValue`
  and `CTCodelistNameValue` nodes.
  But only deactivate if all catalogues that share the codelist have removed that codelist.
  If there is at least one catalogue that shares the codelist but does not remove it, then it is
  considered to be an inconsistency and we need to log that in some sort (TO BE DEFINED).
  QUESTION: We may need to specify that we have to look only at the different package that have the same publication date (same Package date) no?

  > Example: We have imported the package 'ADaM CT 2019-03-29' which includes nine codelists.
  Let's assume in the next package 'ADaM CT 2020-12-20' two of the nine codelists have been removed (see C117745 [ANLPURP] and C117744 [ANLREAS]).
  Those two codelists should now be retired.
  TODO Is it retired even if it is connected to a catalogue different from - in this case - ADaM? WE HAVE TO LOOK AT THIS CONCRETE EXAMPLE THEN!!

- A term was added to a codelist.
  Same story as for the codelists.
  > Example: Between the package 'ADaM CT 2020-06-26' and 'ADaM CT 2020-0925', two terms were added in the Codelist C81224 [DTYPE]: look for C105701 [LLOD] and C174264 [ULOD].

- One or more attributes of an existing term changed.
  If the attribute value was in final version 2.0 then create a new 3.0 version.
  If the attribute value was in retired version 2.0 then create a new 3.0 version.
  Values are not supposed to be in draft version, so that is not applicable.
  > Example: See between ADaM CT 2019-12-20 and ADaM CT 2020-03-27, the Term C158155 that has been updated in both C158114 [GDS02PC] and in C158115 [GDS02PN]

- A term was removed from a codelist -> deactivate the term in that codelist
  > Example: See between SDTM CT 2014-12-19 and SDTM CT 201503-27, the Term C48153 [uL] has been removed. Verify that!



- There is a codelist with the name 'Codelist 001 Name' and another codelist with the name 'Codelist 001 Code'.
  In this case, we will import the terms of 'Codelist 001 Code' interpreting the submission value as
  code_submission_value, we will import the terms of 'Codelist 001 Name' interpreting the submission value as
  name_submission_value.
  NOTE: Here the two Codelist should share the same list of Terms... So when we import the Terms of 'Codelist 001 Name', the script should update the existing terms by just adding the Submission Value as the name_submission_value.
  This is one of the two standard cases. There is no inconsistency logged whatsoever.
  > Cf. cdisc_test_data/case2

- There is a codelist with the name 'Codelist 001 Name' without another codelist with the
  name 'Codelist 001 Code' or 'Codelist 001'. In this case, we will import the terms of 'Codelist 001 Name' interpreting
  the submission value as name_submission_value. In addition, we will log that situation to be an inconsistency.
  The code_submission_value will stay blank here!
  > Cf. cdisc_test_data/case3
  NOTE: We can also look for 'Test Code' or 'Test Name' as most of the pair that we have in the CT are following this rule?...
  BE CAREFUL: One execption: IN SDTM CT, C106480 [DIPARM] and C106481 [DIPARMCD] are named using 'Device Identifier Long Name' and 'Device Identifier Short Name'... THIS IS AN EXCEPTION TO OUR RULE HERE


Is the next really correct? It is not implemented like this.

- There is a codelist with the name 'Codelist 001 Code' without another codelist with the
  name 'Codelist 001 Name' or 'Codelist 001'. In this case, we will import the terms of 'Codelist 001 Code'
  interpreting the submission value as name_submission_value (! name instead of code). And the code_submission_value will stay blank in this case.
  In addition, we will log that situation to be an inconsistency.
  > Cf. cdisc_test_data/case4

## Consistencies (positive cases)

Not yet implemented!

[![Test-Cases 1](~@source/images/cdisc/test_cases/test_cases.svg)](../../images/cdisc/test_cases/test_cases.svg)


## Inconsistencies (negative cases)

[![Test-Cases 2](~@source/images/cdisc/test_cases/test_cases_for_inconsistencies_implemented.svg)](../../images/cdisc/test_cases/test_cases_for_inconsistencies_implemented.svg)


Not yet implemented!

[![Test-Cases Not Implemented](~@source/images/cdisc/test_cases/test_cases_for_inconsistencies_not_implemented.svg)](../../images/cdisc/test_cases/test_cases_for_inconsistencies_not_implemented.svg)

