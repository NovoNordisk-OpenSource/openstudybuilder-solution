import re
from pathlib import Path

from common.config import settings
from common.exceptions import NotFoundException, ValidationException

STYLESHEET_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9-]+$")


class OdmXmlStylesheetService:
    @staticmethod
    def _stylesheet_dir() -> Path:
        return Path(settings.xml_stylesheet_dir_path).resolve(strict=True)

    @staticmethod
    def _iter_stylesheet_files() -> list[Path]:
        stylesheet_dir = OdmXmlStylesheetService._stylesheet_dir()
        stylesheet_files = []

        for file in stylesheet_dir.iterdir():
            if file.is_file() and file.suffix == ".xsl":
                resolved_file = file.resolve(strict=True)
                if resolved_file.parent == stylesheet_dir:
                    stylesheet_files.append(resolved_file)

        return sorted(stylesheet_files)

    @staticmethod
    def get_available_stylesheet_names():
        """
        Returns a list of available XML stylesheet names based on existing files in folder `settings.xml_stylesheet_dir_path`.

        Returns:
            list[str]: A list of available XML stylesheet names.
        """
        return [file.stem for file in OdmXmlStylesheetService._iter_stylesheet_files()]

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
        if not STYLESHEET_NAME_PATTERN.fullmatch(stylesheet):
            raise ValidationException(
                msg="Stylesheet name must only contain letters, numbers and hyphens.",
            )

        for file in OdmXmlStylesheetService._iter_stylesheet_files():
            if file.stem == stylesheet:
                return str(file)

        raise NotFoundException(
            msg=f"Stylesheet with Name '{stylesheet}' doesn't exist.",
        )

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
