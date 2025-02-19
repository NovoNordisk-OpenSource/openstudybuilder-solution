import re
from os import listdir, path

from common.config import XML_STYLESHEET_DIR_PATH
from common.exceptions import NotFoundException, ValidationException


class OdmXmlStylesheetService:
    @staticmethod
    def get_available_stylesheet_names():
        """
        Returns a list of available XML stylesheet names based on existing files in folder `XML_STYLESHEET_DIR_PATH`.

        Returns:
            list[str]: A list of available XML stylesheet names.
        """
        dir_files = listdir(XML_STYLESHEET_DIR_PATH)

        rs = []
        for file in dir_files:
            if file.endswith(".xsl"):
                rs.append(file.removesuffix(".xsl"))
        rs.sort()
        return rs

    @staticmethod
    def get_xml_filename_by_name(stylesheet: str):
        """
        Returns the filename of the XML stylesheet with the given name.

        Args:
            stylesheet (str): The name of the XML stylesheet.

        Returns:
            str: The filename of the XML stylesheet.

        Raises:
            ValidationException: If the stylesheet name contains characters other than letters, numbers, and hyphens.
            NotFoundException: If the stylesheet with the given name is not found.
        """
        ValidationException.raise_if(
            re.search("[^a-zA-Z0-9-]", stylesheet),
            msg="Stylesheet name must only contain letters, numbers and hyphens.",
        )

        filename = XML_STYLESHEET_DIR_PATH + stylesheet + ".xsl"

        NotFoundException.raise_if_not(
            path.exists(filename),
            msg=f"Stylesheet with Name '{stylesheet}' doesn't exist.",
        )

        return filename

    @staticmethod
    def get_specific_stylesheet(stylesheet: str):
        """
        Returns the contents of the XML stylesheet with the given name.

        Args:
            stylesheet (str): The name of the XML stylesheet.

        Returns:
            str: The contents of the XML stylesheet.

        Raises:
            ValidationException: If the stylesheet name contains characters other than letters, numbers, and hyphens.
            BusinessLogicException: If the stylesheet with the given name is not found.
        """
        with open(
            OdmXmlStylesheetService.get_xml_filename_by_name(stylesheet),
            mode="r",
            encoding="utf-8",
        ) as file:
            return file.read()
