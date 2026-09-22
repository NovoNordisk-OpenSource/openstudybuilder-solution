import datetime
from src.scripts.entities.cdisc_data_models.version import Version
from src.scripts.entities.cdisc_data_models.data_model_type import (
    DataModelType,
)
from src.scripts.entities.cdisc_data_models.data_model_class import (
    DataModelClass,
)
from src.scripts.entities.cdisc_data_models.data_model_scenario import (
    DataModelScenario,
)
from src.scripts.entities.cdisc_data_models.data_model_variable import (
    DataModelVariable,
)


class DataModelImport:
    def __init__(
        self, library: str, catalogue: str, version_number: str, author_id: str
    ):
        self.import_date_time: str = datetime.datetime.now().astimezone().isoformat()
        self.library: str = library
        self.catalogue: str = catalogue
        self.version_number: str = version_number
        self.author_id: str = author_id
        self.automatic_resolution_done: bool = False

        self.__version: Version = None

        # a dictionary used as hash map where
        # - the key is the name of the class and
        # - the value is the Class object
        self.__classes: dict[str, DataModelClass] = dict()
        self.__scenarios: dict[str, DataModelScenario] = dict()
        self.__variables: dict[str, DataModelVariable] = dict()

    def get_version(self):
        return self.__version

    def add_version(self, version: Version):
        self.__version = version

    def get_type(self):
        return self.__data_model_type

    def set_type(self, data_model_type: DataModelType):
        self.__data_model_type = data_model_type

    def get_implements_data_model(self):
        return self.__implements_data_model

    def set_implements_data_model(self, data_model_href):
        self.__implements_data_model: str = data_model_href

    def get_classes(self):
        return self.__classes.values()

    def get_classes_as_dict(self):
        return self.__classes

    def get_variables_as_dict(self):
        return self.__variables

    def merge_class(self, name: str) -> DataModelClass:
        _class: DataModelClass = self.__classes.get(name, DataModelClass(name))
        self.__classes[name] = _class
        return _class

    def get_variables(self):
        return self.__variables.values()

    def merge_variable(self, href: str) -> DataModelVariable:
        _variable: DataModelVariable = self.__variables.get(
            href, DataModelVariable(href)
        )
        self.__variables[href] = _variable
        return _variable

    def get_scenarios(self):
        return self.__scenarios.values()

    def merge_scenario(
        self, version: Version, scenario_json_data: dict
    ) -> DataModelScenario:
        href = (
            scenario_json_data.get("_links", None).get("self", None).get("href", None)
        )
        class_name = scenario_json_data.get("domainName", None)

        _scenario: DataModelScenario = self.__scenarios.get(
            href, DataModelScenario(href)
        )
        self.__scenarios[href] = _scenario
        # If a class (dataset) already exists with the scenario's parent class name
        # And it has variables
        # Create a new default scenario with the same name as the class
        # For example : '/mdr/cdashig/2-3/scenarios/DA'
        # And move the variables to it

        parent_class = self.get_classes_as_dict()[class_name]
        parent_class_variables = [v.href for v in parent_class.get_variables()]
        if len(parent_class_variables) > 0:
            root_href = href.rsplit("/", 1)[0] + "/" + class_name
            _root_scenario: DataModelScenario = DataModelScenario(href=root_href)
            self.__scenarios[root_href] = _root_scenario

            _root_scenario.set_attributes(
                title=class_name,
                label=f"{class_name} - Default",
                ordinal="0",
                dataset_href=scenario_json_data.get("_links", None)
                .get("parentDomain", None)
                .get("href", None),
            )

            # Add variables to root scenario
            all_variables: list[DataModelVariable] = self.get_variables_as_dict()
            root_variables = [all_variables[key] for key in parent_class_variables]
            _root_scenario.add_variables(root_variables)
            version.add_scenario(_root_scenario)

            # Remove variables from parent class
            parent_class.drop_variables()

        return _scenario
