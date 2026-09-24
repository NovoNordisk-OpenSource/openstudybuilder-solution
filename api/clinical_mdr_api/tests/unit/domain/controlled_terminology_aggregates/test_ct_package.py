import datetime

from clinical_mdr_api.domains.controlled_terminologies.ct_package import CTPackageAR
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_ct_package() -> CTPackageAR:
    random_ct_package = CTPackageAR.from_repository_values(
        uid=random_str(),
        catalogue_name=random_str(),
        name=random_str(),
        label=random_str(),
        description=random_str(),
        href=random_str(),
        registration_status=random_str(),
        source=random_str(),
        extends_package=None,
        import_date=datetime.datetime.now(datetime.timezone.utc),
        effective_date=datetime.date(year=2020, month=6, day=26),
        author_id=random_str(),
        author_username=random_str(),
    )
    return random_ct_package
