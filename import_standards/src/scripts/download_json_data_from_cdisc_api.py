"""
This script downloads the JSON data (CT, Data Models and IGs) from the CDISC API.
"""

import json
from typing import Sequence
from os import listdir, environ, path
from pathlib import Path
import requests
from requests.exceptions import HTTPError
from neo4j.exceptions import ServiceUnavailable
from src.scripts.entities.cdisc_data_models.version import Version
from src.scripts.entities.cdisc_data_models.data_model_import import (
    DataModelImport,
)
from src.scripts.utils import get_cdisc_neo4j_driver, is_older_than

NEO4J_MDR_DATABASE = environ.get("NEO4J_MDR_DATABASE", "neo4j")
CDISC_IMPORT_DATABASE = environ.get("NEO4J_CDISC_IMPORT_DATABASE", "cdisc")
AUTH_TOKEN = environ.get("CDISC_AUTH_TOKEN")
HEADERS = {"api-key": AUTH_TOKEN, "Accept": "application/json"}
BASE_URL = environ.get("CDISC_BASE_URL")


def find_downloaded_packages(directory: str) -> set[str]:
    """
    Returns the ids of the packages already stored as JSON files in <directory>,
    e.g. {"sdtmct-2019-12-20", "adamct-2014-09-26"}.

    The id is the file name without the ".json" extension, which is how
    download_packages_data() names the files it writes.
    """
    if not path.isdir(directory):
        return set()

    return {
        path.splitext(name)[0].lower()
        for name in listdir(directory)
        if path.splitext(name)[1] == ".json"
    }


def download_missing_packages(to_directory: str, not_older_than: str | None = None):
    """
    Downloads every package the CDISC REST API offers that is not already
    present as a JSON file in <to_directory>.
    Stores the data in JSON files on disc.

    The set of files on disc is the only thing consulted - no database is
    involved. That keeps the check per package rather than per effective date,
    so a gap in one catalogue is filled even when another catalogue is newer.

    :param not_older_than: string (YYYY-MM-DD), optional. When given, packages
        with an earlier effective date are left alone. Without it the whole
        history is synced.
    """

    already_downloaded = find_downloaded_packages(to_directory)
    print(
        f"Found {len(already_downloaded)} already downloaded package(s) "
        f"in directory='{to_directory}'."
    )
    if not_older_than is not None:
        print(f"Ignoring packages with an effective_date before '{not_older_than}'.")

    available_packages_in_api = get_available_packages_meta_data_from_api()

    packages_to_load = []
    skipped_as_too_old = 0
    for package in available_packages_in_api["_links"]["packages"]:
        href = package["href"]
        # example for the href property: "/mdr/ct/packages/adamct-2014-09-26"
        # the package_id is the part of the href after the last slash (/)
        # e.g. "adamct-2014-09-26"
        package_id = path.basename(href)
        # the effective date is the last three dash separated parts
        # e.g. "2014-09-26", and the catalogue name is everything before it.
        # Split from the right: catalogue names may contain a dash themselves
        # ("define-xmlct", "qs-ftct").
        catalogue_name, *date_parts = package_id.rsplit("-", 3)
        effective_date = "-".join(date_parts)
        package["catalogue_name"] = catalogue_name.upper()
        package["effective_date"] = effective_date

        if package_id.lower() in already_downloaded:
            continue
        if not_older_than is not None and is_older_than(effective_date, not_older_than):
            skipped_as_too_old += 1
            continue
        packages_to_load.append(package)

    print(
        f"The API offers {len(available_packages_in_api['_links']['packages'])} package(s), "
        f"{len(packages_to_load)} of which are missing"
        + (
            f" ({skipped_as_too_old} skipped as too old)."
            if skipped_as_too_old
            else "."
        )
    )

    if len(packages_to_load) > 0:
        download_packages_data(packages_to_load, to_directory)
    else:
        print(" -> No packages found for downloading.")


def get_available_packages_meta_data_from_api() -> dict:
    """
    Gets the CT packages list from the CDISC REST API.

    The JSON result has the following form:
    {
        "_links": {
            "self": {
                "href": "/mdr/ct/packages",
                "title": "Product Group Terminology",
                "type": "Controlled Terminology Package List"
            },
            "packages": [
                {
                    "href": "/mdr/ct/packages/sdtmct-2019-12-20",
                    "title": "SDTM Controlled Terminology Package 40 Effective 2019-12-20",
                    "type": "Terminology"
                }
            ]
        }
    }
    """
    response = requests.get(BASE_URL + "/mdr/ct/packages", headers=HEADERS, timeout=60)
    response.raise_for_status()
    return response.json()


def download_packages_data(packages_to_download: Sequence, to_directory: str):
    """
    Downloads the CDISC CT package data for those packages specified by <packages_to_download>.
    Stores the data in JSON files on disc.

    Callers are expected to have filtered out the packages that are already on
    disc - see find_downloaded_packages().

    :param packages_to_download: a list of those packages that shall be downloaded.
    """

    create_cdisc_data_dir(to_directory)
    print("")
    print(f"Storing files in directory='{to_directory}'.")
    step = 1
    number_of_packages = len(packages_to_download)
    for package in packages_to_download:
        package_id = package["catalogue_name"] + "-" + package["effective_date"]
        print(
            f"  Step: {step}/{number_of_packages} - Downloading package '{package_id}'."
        )
        try:
            response = requests.get(
                BASE_URL + package["href"], headers=HEADERS, timeout=60
            )
            response.raise_for_status()
            package_data = response.json()
        except HTTPError as http_err:
            print(f"    HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"    Other error occurred: {err}")
        else:
            filename = package_id.split("/")[-1].lower() + ".json"
            with open(
                path.join(to_directory, filename), "w", encoding="utf-8"
            ) as ctpkg_file:
                ctpkg_file.write(json.dumps(package_data))
                ctpkg_file.write("\n")
        step += 1


def get_available_model_versions_meta_data_from_api() -> json:
    """
    Gets the Models and IG versions list from the CDISC REST API.
    Several endpoints need to be called.

    The general JSON result has the following form:
    {
        "_links": {
            "self": {
                "href": "/mdr/products/DataTabulation",
                "title": "Product Group Data Tabulation",
                "type": "CDISC Library Product Group"
            },
            "sdtm": [
                {
                    "href": "/mdr/sdtm/1-8",
                    "title": "Study Data Tabulation Model Version 1.8 (Final)",
                    "type": "Foundational Model"
                }
            ],
            "sdtmig": [
                {
                    "href": "/mdr/sdtmig/3-3",
                    "title": "Study Data Tabulation Model Implementation Guide: Human Clinical Trials Version 3.3 (Final)",
                    "type": "Implementation Guide"
                }
            ],
            }
        }

    Returns:
        json: Concatenated json with objects returned from the different endpoints
        Note : _links top level and self objects are removed before concatenating to prevent conflicts
    """
    # Get data tabulation (SDTM, SEND)
    response = requests.get(
        BASE_URL + "/mdr/products/DataTabulation", headers=HEADERS, timeout=60
    )
    response.raise_for_status()
    data_tabulation = response.json()
    if "self" in data_tabulation["_links"]:
        del data_tabulation["_links"]["self"]

    # Get data collection (CDASH)
    response = requests.get(
        BASE_URL + "/mdr/products/DataCollection", headers=HEADERS, timeout=60
    )
    response.raise_for_status()
    data_collection = response.json()
    if "self" in data_collection["_links"]:
        del data_collection["_links"]["self"]

    # Get data analysis (ADaM)
    # response = requests.get(BASE_URL + "/mdr/products/DataAnalysis", headers=HEADERS)
    # response.raise_for_status()
    # data_analysis = response.json()
    # if "self" in data_analysis["_links"]:
    #     del data_analysis["_links"]["self"]

    return {**data_tabulation["_links"], **data_collection["_links"]}


def download_newer_data_model_versions_than(
    last_available_versions: dict, to_directory: str, library: str = "CDISC"
):
    """
    Downloads the versions from the CDISC REST API where the version number is higher than the specified
    versions for each catalogue, as defined in <last_available_versions>.
    Stores the data in JSON files on disc.

    Args:
        last_available_versions (dict): Dictionary with last version number available for each catalogue. e.g. {"sdtm": "1.8", "cdashig": "1.1"}
        to_directory (str): Directory where to store the downloaded data
        library (str): Library name to use in the DataModelImport object. Default is "CDISC"
    """

    available_versions_in_api = get_available_model_versions_meta_data_from_api()
    for catalogue in available_versions_in_api:
        versions_to_load = []
        versions = available_versions_in_api[catalogue]
        catalogue = catalogue.upper()
        for _version in versions:
            href = _version["href"]
            data_model_type = _version["type"]
            # example for the href property: "/mdr/sdtm/1-8"
            # the version number is the part of the href after the last slash (/) for all except ADaM
            # For ADaM, the href is : "/mdr/adam/adamig-1-1" so version is the part after last slash without 'adamig'
            version_number = path.basename(href)

            data_model_import = DataModelImport(
                library=library,
                catalogue=catalogue,
                version_number=version_number,
                author_id="TMP",
            )
            if (catalogue not in last_available_versions) or (
                catalogue in last_available_versions
                and version_number not in last_available_versions[catalogue]
            ):
                version = Version(data_model_import, version_number)
                version.set_catalogue_name(catalogue)
                version.set_href(href)
                versions_to_load.append(version)

        if len(versions_to_load) > 0:
            download_versions_data(catalogue, versions_to_load, to_directory)
        else:
            print(f" -> No versions in catalogue {catalogue} found for downloading.")


def download_versions_data(
    catalogue: str,
    versions_to_download: Sequence[Version],
    to_directory: str,
):
    """
    Downloads the CDISC Data Model version data for those versions specified by <versions_to_download>.
    Stores the data in JSON files on disc.

    If the corresponding JSON files are already present for one or more versions, those versions will be skipped.

    :param catalogue: name of the catalogue
    :param type: type of the model (Foundational Model or Implementation Guide)
    :param versions_to_download: a list of those versions that shall be downloaded.
    :param to_directory: directory in which to download the files
    """
    sub_directory = f"{to_directory}/{catalogue}/models"
    create_cdisc_data_dir(sub_directory)
    print("")
    print(f"Storing files in directory='{to_directory}{catalogue}.")
    existing_versions = set(
        [
            path.splitext(path.basename(x))[0]
            for x in listdir(sub_directory)
            if path.splitext(x)[1] == ".json"
        ]
    )
    step = 1
    number_of_versions = len(versions_to_download)
    for version in versions_to_download:
        version_number = version.get_version_number()
        if version_number in existing_versions:
            print(
                f" Catalogue {catalogue} - Step: {step}/{number_of_versions} - Version '{version_number}' already downloaded."
            )
        else:
            print(
                f"  Catalogue {catalogue} - Step: {step}/{number_of_versions} - Downloading version '{version_number}'."
            )
            try:
                response = requests.get(
                    BASE_URL + version.href, headers=HEADERS, timeout=60
                )
                response.raise_for_status()
                version_data = response.json()
            except HTTPError as http_err:
                print(f"    HTTP error occurred: {http_err}")
            except Exception as err:
                print(f"    Other error occurred: {err}")
            else:
                filename = f"{version_number}.json"
                with open(
                    path.join(sub_directory, filename), "w", encoding="utf-8"
                ) as version_file:
                    version_file.write(json.dumps(version_data))
                    version_file.write("\n")
        step += 1


def create_cdisc_data_dir(directory: str):
    """
    Create a directory for the downloaded CDISC data.
    """
    try:
        Path(directory).mkdir(0o750, True, True)
    except OSError as error:
        # ignore [Errno 17] File exists
        if error.errno != 17:
            print(error)


def get_latest_data_model_versions():
    """
    Get the latest imported data model versions from the CDISC Import database.
    """

    cdisc_neo4j_driver = get_cdisc_neo4j_driver()

    # If using a staging database, it might not exist yet
    # so we need to create it first
    if CDISC_IMPORT_DATABASE != NEO4J_MDR_DATABASE:
        try:
            with cdisc_neo4j_driver.session(database="system") as session:
                session.run(
                    "CREATE DATABASE $database IF NOT EXISTS",
                    database=CDISC_IMPORT_DATABASE,
                )
        except ServiceUnavailable:
            print("Can't connect to neo4j database, using default latest version")
            return {}

    with cdisc_neo4j_driver.session(database=CDISC_IMPORT_DATABASE) as session:
        with session.begin_transaction() as tx:
            output = {}
            result = tx.run("""
                MATCH (import:DataModelImport)
                WITH import.catalogue as catalogue, collect(import.version_number) AS versions
                RETURN catalogue, versions
                """)
            for record in result.data():
                output[record["catalogue"]] = record["versions"]
            return output


def download_ct_json_data_from_cdisc_api(
    to_directory: str, not_older_than: str | None = None
):
    """
    Download the CT JSON data from the CDISC API.
    """
    download_missing_packages(to_directory, not_older_than)


def download_data_model_json_data_from_cdisc_api(to_directory: str):
    """
    Download the data model JSON data from the CDISC API.
    """
    download_newer_data_model_versions_than(
        get_latest_data_model_versions(), to_directory
    )
