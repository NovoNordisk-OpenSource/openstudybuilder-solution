from importers.run_import_activities import Activities
from importers.run_import_complexity_burdens import ComplexityBurdens
from importers.run_import_compounds import Compounds
from importers.run_import_crfs import Crfs
from importers.run_import_data_suppliers import DataSuppliers
from importers.run_import_dictionaries import Dictionaries
from importers.run_import_e2e import MockdataJsonE2E
from importers.run_import_mockdata import Mockdata
from importers.run_import_mockdatajson import MockdataJson
from importers.run_import_nonstandard_variables import NonStandardVariables
from importers.run_import_response_codelists import ResponseCodelists
from importers.run_import_sponsormodels import SponsorModels
from importers.run_import_standardcodelistfinish import StandardCodelistFinish
from importers.run_import_standardcodelistterms1 import StandardCodelistTerms1
from importers.run_import_standardcodelistterms2 import StandardCodelistTerms2
from importers.run_import_trial_summary_parameters import TrialSummaryParameters
from importers.run_import_unitdefinitions import Units
from importers.run_update_activity_instance_activity_items import (
    ActivityInstanceActivityItems,
)
from importers.utils.metrics import Metrics


def main():
    metr = Metrics()

    # Migrate the libraries (SNOMED etc)
    dictmigrator = Dictionaries(metrics_inst=metr)
    dictmigrator.run()

    # Import standard codelist terms, part 1
    standardterms1 = StandardCodelistTerms1(metrics_inst=metr)
    standardterms1.run()
    # raise RuntimeError("stop here")
    # Import standard codelist terms, part 2
    standardterms2 = StandardCodelistTerms2(metrics_inst=metr)
    standardterms2.run()
    # raise RuntimeError("stop here")
    # Import unit definitions
    units = Units(metrics_inst=metr)
    units.run()

    activities = Activities(metrics_inst=metr)
    activities.run()

    activity_items = ActivityInstanceActivityItems(metrics_inst=metr)
    activity_items.run()

    complexity_burdens = ComplexityBurdens(metrics_inst=metr)
    complexity_burdens.run()

    # Import sponsor models
    sponsor_models = SponsorModels(metrics_inst=metr)
    sponsor_models.run()

    # Import trial summary parameters
    trial_summary_params = TrialSummaryParameters(metrics_inst=metr)
    trial_summary_params.run()

    # Finish up sponsor library
    finishing = StandardCodelistFinish(metrics_inst=metr)
    finishing.run()

    # Import non-standard variables (depends on standard codelists & activity item classes)
    nonstandard_variables = NonStandardVariables(metrics_inst=metr)
    nonstandard_variables.run()

    # Import data suppliers
    data_suppliers = DataSuppliers(metrics_inst=metr)
    data_suppliers.run()

    # Import compounds
    compounds = Compounds(metrics_inst=metr)
    compounds.run()

    # Import crfs
    crfs = Crfs(metrics_inst=metr)
    crfs.run()

    # Import mock data
    mockdata = Mockdata(metrics_inst=metr)
    mockdata.run()

    # Import mock data from json
    mockdatajson = MockdataJson(metrics_inst=metr)
    mockdatajson.run()

    # Import E2E specific data from json
    mockdatae2e = MockdataJsonE2E(metrics_inst=metr)
    mockdatae2e.run()

    # Import response codelists
    response_codelists = ResponseCodelists(metrics_inst=metr)
    response_codelists.run()

    # Display metrics
    metr.print_sorted_by_key()
    metr.print_sorted_by_value()


if __name__ == "__main__":
    main()
