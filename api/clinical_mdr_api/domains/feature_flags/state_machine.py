from common.exceptions import BusinessLogicException


class FeatureFlagStateMachine:
    @staticmethod
    def ensure_can_update(status: str | None) -> None:
        BusinessLogicException.raise_if(
            status != "Final",
            msg="Only Final feature flags can be updated.",
        )

    @staticmethod
    def ensure_can_inactivate(status: str | None) -> None:
        BusinessLogicException.raise_if(
            status != "Final",
            msg="Only Final feature flags can be inactivated.",
        )

    @staticmethod
    def ensure_can_reactivate(status: str | None) -> None:
        BusinessLogicException.raise_if(
            status != "Retired",
            msg="Only Retired feature flags can be reactivated.",
        )
