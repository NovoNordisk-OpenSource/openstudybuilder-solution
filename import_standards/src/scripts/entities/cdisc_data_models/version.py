from typing import Sequence, OrderedDict

from src.scripts.entities.cdisc_data_models.data_model_type import (
    DataModelType,
)
from src.scripts.entities.cdisc_data_models.data_model_class import (
    DataModelClass,
)
from src.scripts.entities.cdisc_data_models.data_model_scenario import (
    DataModelScenario,
)


class Version:
    def __init__(self, data_model_import, version_number: str):
        self.__data_model_import = data_model_import
        self.__version_number = version_number

        self.__implements_data_model: str = None
        self.__classes: set[DataModelClass] = set()
        self.__scenarios: set[DataModelScenario] = set()

        self.href = ""

    def get_data_model_import(self):
        return self.__data_model_import

    def get_version_number(self) -> str:
        return self.__version_number

    def get_implements_data_model(self) -> str:
        return self.__implements_data_model

    def get_classes(self) -> Sequence[DataModelClass]:
        return list(self.__classes)

    def get_scenarios(self) -> Sequence[DataModelScenario]:
        return list(self.__scenarios)

    def add_scenario(self, scenario: DataModelScenario):
        self.__scenarios.add(scenario)

    def set_name(self, name) -> None:
        self.name: str = name

    def set_catalogue_name(self, catalogue_name) -> None:
        self.catalogue_name: str = catalogue_name

    def set_href(self, href) -> None:
        self.href: str = href

    def set_implements_data_model(self, data_model_href) -> None:
        self.__implements_data_model: str = data_model_href

    def __set_attributes(
        self,
        name: str,
        label: str,
        description: str,
        source: str,
        effective_date: str,
        registration_status: str,
        data_model_type: str,
        href: str,
        prior_version: str,
    ) -> None:
        self.set_name(name)
        self.label: str = label
        self.description: str = description
        self.source: str = source
        self.effective_date: str = effective_date
        self.registration_status: str = registration_status
        self.data_model_type: str = data_model_type
        self.href: str = href
        self.prior_version: str = prior_version

    def load_from_json_data(self, version_json_data) -> None:
        self.__load_json_version_data(version_json_data)

    def __load_json_version_data(self, version_json_data) -> None:
        data_model_type = self.__get_data_model_type(version_json_data)
        self.__set_attributes(
            name=version_json_data.get("name", None),
            label=version_json_data.get("label", None),
            description=version_json_data.get("description", None),
            source=version_json_data.get("source", None),
            effective_date=version_json_data.get("effectiveDate", None),
            registration_status=version_json_data.get("registrationStatus", "Final"),
            data_model_type=data_model_type,
            href=self.__get_href(version_json_data),
            prior_version=version_json_data.get("_links", {})
            .get("priorVersion", {})
            .get("href", None),
        )
        if data_model_type == DataModelType.IMPLEMENTATION.value:
            self.set_implements_data_model(self.__get_model_href(version_json_data))

    def load_class_from_json_data(
        self, class_json_data, version_json_data, catalogue
    ) -> None:
        data_model_type = self.__get_data_model_type(version_json_data)
        implements_class = None
        if data_model_type == DataModelType.IMPLEMENTATION.value:
            # The parentClass href identifies the class implemented by the dataset, on the IG side
            parent_class_href = (
                class_json_data.get("_links", {})
                .get("parentClass", {})
                .get("href", None)
            )
            # This can then be matched with the actual class, on the Model side
            if "modelDataset" in class_json_data.get("_links"):
                implements_class = (
                    class_json_data.get("_links", {})
                    .get("modelDataset", {})
                    .get("href", None)
                )
            else:
                implements_class = [
                    x.get("_links", {}).get("modelClass", {}).get("href", None)
                    for x in version_json_data.get("classes", [])
                    if x.get("_links", {}).get("self", {}).get("href", None)
                    == parent_class_href
                ]
                implements_class = implements_class[0] if implements_class else None

        class_name = class_json_data.get("name", None)
        class_ordinal = class_json_data.get("ordinal")
        if (
            data_model_type == DataModelType.FOUNDATIONAL.value
            and "datasets" in class_json_data
            and len(class_json_data.get("datasets", [])) > 0
        ):
            for dataset in class_json_data.get("datasets", []):
                self.__parse_and_create_class(
                    catalogue=catalogue,
                    data_model_type=data_model_type,
                    class_json_data=dataset,
                    name="-".join([class_name, dataset.get("name", None)]),
                    implements_class=implements_class,
                    is_class_dataset=True,
                    class_ordinal=".".join(
                        [class_ordinal, dataset.get("ordinal", None)]
                    ),
                )
        elif (
            catalogue == "CDASH"
            and "fields" in class_json_data
            and len(class_json_data.get("fields", [])) > 0
        ):
            parent_class = next(
                _class
                for _class in self.get_classes()
                if _class.href
                == class_json_data.get("_links", {})
                .get("parentClass", {})
                .get("href", None)
            )
            self.__parse_and_create_class(
                catalogue=catalogue,
                data_model_type=data_model_type,
                class_json_data=class_json_data,
                name="-".join([parent_class.name, class_name]),
                implements_class=implements_class,
                is_class_dataset=True,
                class_ordinal=".".join([parent_class.ordinal, class_ordinal]),
            )
        else:
            self.__parse_and_create_class(
                catalogue=catalogue,
                data_model_type=data_model_type,
                class_json_data=class_json_data,
                name=class_name,
                class_ordinal=class_ordinal,
                implements_class=implements_class,
            )

    def load_from_csv_data(
        self, catalogue: str, version_csv_data, data_model_type: str
    ) -> None:
        self.__load_csv_version_data(catalogue, version_csv_data, data_model_type)

    def __load_csv_version_data(
        self, catalogue: str, version_csv_data, data_model_type: str
    ) -> None:
        self.__set_attributes(
            name=version_csv_data.get("name", None),
            label=version_csv_data.get("label", None),
            description=version_csv_data.get("description", None),
            source=version_csv_data.get("source", None),
            registration_status=version_csv_data.get("registration_status", "Final"),
            effective_date=version_csv_data.get("release_date", None),
            data_model_type=data_model_type,
            href=version_csv_data.get("href", None),
            prior_version=version_csv_data.get("prior_version", None),
        )
        if data_model_type == DataModelType.IMPLEMENTATION:
            implements_href = "/".join(
                [
                    "/mdr",
                    catalogue.lower(),
                    self.get_version_number(),
                ]
            )
            self.set_implements_data_model(implements_href)

    def load_class_from_csv_data(
        self,
        class_csv_data: OrderedDict,
        data_model_type: DataModelType,
        catalogue: str,
        variables_csv_data: Sequence[OrderedDict],
    ) -> None:
        implements_class = None
        is_class_dataset = False
        if data_model_type == DataModelType.IMPLEMENTATION:
            is_class_dataset = True
            implements_class = "/".join(
                [
                    "/mdr",
                    catalogue.lower()[:-2],
                    self.get_version_number(),
                    "classes",
                    class_csv_data.get("dataset_class", None),
                ]
            )

        class_name = class_csv_data.get("name", None)
        class_ordinal = class_csv_data.get("order")
        self.__parse_and_create_csv_class(
            catalogue=catalogue,
            data_model_type=data_model_type,
            class_csv_data=class_csv_data,
            name=class_name,
            class_ordinal=class_ordinal,
            implements_class=implements_class,
            variables_csv_data=variables_csv_data,
            is_class_dataset=is_class_dataset,
        )

    def __parse_and_create_csv_class(
        self,
        catalogue: str,
        data_model_type: DataModelType,
        class_csv_data: OrderedDict,
        name: str,
        implements_class: str,
        class_ordinal: str,
        variables_csv_data: Sequence[OrderedDict],
        is_class_dataset: bool = False,
    ):
        _class: DataModelClass = self.get_data_model_import().merge_class(name)
        _class.set_attributes(
            title=class_csv_data.get("title", None),
            label=class_csv_data.get("label"),
            description=class_csv_data.get("description"),
            ordinal=class_ordinal,
            href=class_csv_data.get("href", None),
            implements_class=implements_class,
            prior_version=class_csv_data.get("prior_version", None),
        )

        _class.load_variables_from_csv_data(
            class_csv_data=class_csv_data,
            catalogue=catalogue,
            data_model_import=self.get_data_model_import(),
            data_model_type=data_model_type,
            variables_data=variables_csv_data,
            is_class_dataset=is_class_dataset,
        )

        self.__add_class(_class)

    def __parse_and_create_class(
        self,
        catalogue,
        data_model_type,
        class_json_data,
        name,
        implements_class,
        class_ordinal,
        is_class_dataset: bool = False,
    ):
        _class: DataModelClass = self.get_data_model_import().merge_class(name)
        _class.set_attributes(
            title=class_json_data.get("_links", {}).get("self", {}).get("title", None),
            label=class_json_data.get("label"),
            description=class_json_data.get("description"),
            ordinal=class_ordinal,
            href=class_json_data.get("_links", {}).get("self", {}).get("href", None),
            implements_class=implements_class,
            prior_version=class_json_data.get("_links", {})
            .get("priorVersion", {})
            .get("href", None),
            subclasses=[
                subclass.get("href", None)
                for subclass in class_json_data.get("_links", {}).get("subclasses", [])
            ],
        )

        _class.load_variables_from_json_data(
            class_json_data=class_json_data,
            catalogue=catalogue,
            data_model_import=self.get_data_model_import(),
            data_model_type=data_model_type,
            is_class_dataset=is_class_dataset,
        )

        self.__add_class(_class)

    def load_scenario_from_json_data(
        self,
        scenario_json_data,
        catalogue,
        data_model_type,
    ):
        data_model_import = self.get_data_model_import()
        _scenario: DataModelScenario = data_model_import.merge_scenario(
            self,
            scenario_json_data=scenario_json_data,
        )

        _scenario.set_attributes(
            title=scenario_json_data.get("_links", None)
            .get("self", None)
            .get("title", None),
            label=scenario_json_data.get("scenario", None),
            ordinal=scenario_json_data.get("ordinal", None),
            dataset_href=scenario_json_data.get("_links", None)
            .get("parentDomain", None)
            .get("href", None),
        )

        _scenario.load_variables_from_json_data(
            scenario_json_data=scenario_json_data,
            catalogue=catalogue,
            data_model_import=data_model_import,
            data_model_type=data_model_type,
        )

        self.add_scenario(_scenario)

    def __get_data_model_type(self, version_json_data) -> str:
        data_model_type = None
        links = version_json_data.get("_links", None)
        if links:
            _self = links.get("self", None)
            if _self:
                data_model_type = _self.get("type", None)
        return data_model_type

    def __get_href(self, version_json_data) -> str:
        href = None
        links = version_json_data.get("_links", None)
        if links:
            _self = links.get("self", None)
            if _self:
                href = _self.get("href", None)
        return href

    def __get_model_href(self, version_json_data) -> str:
        model = None
        links = version_json_data.get("_links", None)
        if links:
            _self = links.get("model", None)
            if _self:
                model = _self.get("href", None)
        return model

    def __add_class(self, _class: DataModelClass) -> None:
        self.__classes.add(_class)
