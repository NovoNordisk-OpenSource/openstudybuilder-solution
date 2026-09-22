from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class CTPackageAR:
    _uid: str
    catalogue_name: str
    name: str
    label: str | None
    description: str | None
    href: str | None
    registration_status: str | None
    source: str | None
    extends_package: str | None
    import_date: datetime
    effective_date: date
    author_id: str
    author_username: str

    @property
    def uid(self) -> str:
        return self._uid

    @staticmethod
    def from_repository_values(
        uid: str,
        catalogue_name: str,
        name: str,
        label: str | None,
        description: str | None,
        href: str | None,
        registration_status: str | None,
        source: str | None,
        extends_package: str | None,
        import_date: datetime,
        effective_date: date,
        author_id: str,
        author_username: str,
    ):
        return CTPackageAR(
            _uid=uid,
            catalogue_name=catalogue_name,
            name=name,
            label=label,
            description=description,
            href=href,
            registration_status=registration_status,
            source=source,
            extends_package=extends_package,
            import_date=import_date,
            effective_date=effective_date,
            author_id=author_id,
            author_username=author_username,
        )
