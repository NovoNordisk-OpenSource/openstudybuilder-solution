"""Custom exceptions."""

from typing import Any

from fastapi import status
from fastapi.security import SecurityScopes
from starlette.datastructures import MutableHeaders


class MDRApiBaseException(Exception):
    """
    A base exception class for the MDR API.

    Attributes:
        status_code (int): The HTTP status code for the exception. Defaults to 500.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, msg):
        self.msg = msg
        self.headers = MutableHeaders()
        super().__init__(msg)


class InternalServerError(MDRApiBaseException):
    """
    An exception raised when an unexpected error occurs in the server.

    Attributes:
        status_code (int): The HTTP status code for the exception (500).
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, msg: str | Exception | None = None):
        """
        Default message is: Something went wrong on our end.

        Args:
            msg (str | None): An optional custom error message. If not specified, a default message will be used.
        """
        super().__init__(msg or "Something went wrong on our end.")


class BusinessLogicException(MDRApiBaseException):
    """
    An exception raised when a request could not be completed because it did not pass a business rule check.

    Attributes:
        status_code (int): The HTTP status code for the exception (400).
    """

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        resource_name: str | None = "Resource",
        field_value: str | None = None,
        field_name: str | None = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Default message format is: `resource_name` with `field_name` '`field_value`' didn't pass a business rule.

        Args:
            resource_name (str | None): The name of the resource that does not exist. Defaults to `Resource` if not specified.
            field_value (str | None): The value of the field that was expected to exist.
            field_name (str | None): The name of the field related to the resource. Defaults to `UID` if not provided.
            msg (str | None): An optional custom error message. If not specified, a default message will be constructed using the other parameters.
        """
        if not msg:
            msg = f"{resource_name} with {field_name} '{field_value}' didn't pass a business rule."

        super().__init__(msg)

    @classmethod
    def raise_if(
        cls,
        val: Any,
        resource_name: str = "Resource",
        field_value: str | None = None,
        field_name: str = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Raises BusinessLogicException with status code `400` if `val` evaluates to `True`

        Default message format is: `resource_name` with `field_name` '`field_value`' didn't pass a business rule.
        """

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        if val:
            raise cls(
                resource_name=resource_name,
                field_value=field_value,
                field_name=field_name,
                msg=msg,
            )

    @classmethod
    def raise_if_not(
        cls,
        val: Any,
        resource_name: str = "Resource",
        field_value: str | None = None,
        field_name: str = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Raises BusinessLogicException with status code `400` if `val` evaluates to `False`

        Default message format is: `resource_name` with `field_name` '`field_value`' didn't pass a business rule.
        """

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        cls.raise_if(
            val=not val,
            resource_name=resource_name,
            field_value=field_value,
            field_name=field_name,
            msg=msg,
        )


class VisitsAreNotEqualException(BusinessLogicException):
    """
    Raises VisitsAreNotEqual with status code `400` if `val` evaluates to `False`
    The exception was created as one endpoint can throw 400 status_codes in different cases.
    In one of the case UI client should distinguish the situation and perform specific action.
    The UI client will expect `VisitsAreNotEqualException` to be thrown in that situation.
    """


class NotAuthenticatedException(MDRApiBaseException):
    """
    An exception raised when the client must authenticate itself or get a fresh token.

    Attributes:
        status_code (int): The HTTP status code for the exception (401).
    """

    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, msg: str, security_scopes: SecurityScopes | None = None):
        super().__init__(msg)
        if security_scopes and security_scopes.scopes:
            self.headers["WWW-Authenticate"] = (
                f'Bearer scope="{security_scopes.scope_str}"'
            )
        else:
            self.headers["WWW-Authenticate"] = "Bearer"


class MethodNotAllowedException(MDRApiBaseException):
    """An exception raised when a method is not allowed for a given resource or in a batch operation."""

    status_code = status.HTTP_405_METHOD_NOT_ALLOWED

    def __init__(
        self,
        method: str | None = None,
        *,
        msg: str | None = None,
    ):
        if not msg:
            msg = "Unsupported method"
            if method:
                msg += f": {method}"
        super().__init__(msg)


class ForbiddenException(MDRApiBaseException):
    """
    An exception raised when a client is identified, but does not have the right to perform the requested action on the resource.

    Attributes:
        status_code (int): The HTTP status code for the exception (403).
    """

    status_code = status.HTTP_403_FORBIDDEN

    def __init__(
        self,
        resource_name: str | None = "Resource",
        field_value: str | None = None,
        field_name: str | None = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Default message format is: Access to `resource_name` with `field_name` '`field_value`' is forbidden.

        Args:
            resource_name (str | None): The name of the resource being accessed. Defaults to `Resource` if not specified.
            field_value (str | None): The value of the field that was expected to exist.
            field_name (str | None): The name of the field related to the resource. Defaults to `UID` if not provided.
            msg (str | None): An optional custom error message. If not specified, a default message will be constructed using the other parameters.
        """
        if not msg:
            msg = f"Access to {resource_name} with {field_name} '{field_value}' is forbidden."

        super().__init__(msg)

    @classmethod
    def raise_if(
        cls,
        val: Any,
        resource_name: str = "Resource",
        field_value: str | None = None,
        field_name: str = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Raises ForbiddenException with status code `401` if `val` evaluates to `True`

        Default message format is: Access to `resource_name` with `field_name` '`field_value`' is forbidden.
        """

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        if val:
            raise cls(
                resource_name=resource_name,
                field_value=field_value,
                field_name=field_name,
                msg=msg,
            )

    @classmethod
    def raise_if_not(
        cls,
        val: Any,
        resource_name: str = "Resource",
        field_value: str | None = None,
        field_name: str = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Raises ForbiddenException with status code `401` if `val` evaluates to `False`

        Default message format is: Access to `resource_name` with `field_name` '`field_value`' is forbidden.
        """

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        cls.raise_if(
            val=not val,
            resource_name=resource_name,
            field_value=field_value,
            field_name=field_name,
            msg=msg,
        )


class NotFoundException(MDRApiBaseException):
    """
    An exception raised when a resource cannot be found.

    Attributes:
        status_code (int): The HTTP status code for the exception (404).
    """

    status_code = status.HTTP_404_NOT_FOUND

    def __init__(
        self,
        resource_name: str | None = "Resource",
        field_value: str | None = None,
        field_name: str | None = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Default message format is: `resource_name` with `field_name` '`field_value`' doesn't exist.

        Args:
            resource_name (str | None): The name of the resource that does not exist. Defaults to `Resource` if not specified.
            field_value (str | None): The value of the field that was expected to exist.
            field_name (str | None): The name of the field related to the resource. Defaults to `UID` if not provided.
            msg (str | None): An optional custom error message. If not specified, a default message will be constructed using the other parameters.
        """
        if not msg:
            msg = f"{resource_name} with {field_name} '{field_value}' doesn't exist."

        super().__init__(msg)

    @classmethod
    def raise_if(
        cls,
        val: Any,
        resource_name: str = "Resource",
        field_value: str | None = None,
        field_name: str = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Raises NotFoundException with status code `404` if `val` evaluates to `True`

        Default message format is: `resource_name` with `field_name` '`field_value`' doesn't exist.
        """

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        if val:
            raise cls(
                resource_name=resource_name,
                field_value=field_value,
                field_name=field_name,
                msg=msg,
            )

    @classmethod
    def raise_if_not(
        cls,
        val: Any,
        resource_name: str = "Resource",
        field_value: str | None = None,
        field_name: str = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Raises NotFoundException with status code `404` if `val` evaluates to `False`

        Default message format is: `resource_name` with `field_name` '`field_value`' doesn't exist.
        """

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        cls.raise_if(
            val=not val,
            resource_name=resource_name,
            field_value=field_value,
            field_name=field_name,
            msg=msg,
        )


class AlreadyExistsException(MDRApiBaseException):
    """
    An exception raised when a resource already exists.

    Attributes:
        status_code (int): The HTTP status code for the exception (409).
    """

    status_code = status.HTTP_409_CONFLICT

    def __init__(
        self,
        resource_name: str | None = "Resource",
        field_value: str | None = None,
        field_name: str | None = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Default message format is: `resource_name` with `field_name` '`field_value`' already exists.

        Args:
            resource_name (str | None): The name of the resource that already exists. Defaults to `Resource` if not specified.
            field_value (str | None): The value of the field that is causing the conflict. This provides specific context for the exception.
            field_name (str | None): The name of the field related to the resource. Defaults to `UID` if not provided.
            msg (str | None): An optional custom error message. If not specified, a default message will be constructed using the other parameters.
        """
        if not msg:
            msg = f"{resource_name} with {field_name} '{field_value}' already exists."

        super().__init__(msg)

    @classmethod
    def raise_if(
        cls,
        val: Any,
        resource_name: str = "Resource",
        field_value: str | None = None,
        field_name: str = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Raises AlreadyExistsException with status code `409` if `val` evaluates to `True`

        Default message format is: `resource_name` with `field_name` '`field_value`' already exists.
        """

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        if val:
            raise cls(
                resource_name=resource_name,
                field_value=field_value,
                field_name=field_name,
                msg=msg,
            )

    @classmethod
    def raise_if_not(
        cls,
        val: Any,
        resource_name: str = "Resource",
        field_value: str | None = None,
        field_name: str = "UID",
        *,
        msg: str | None = None,
    ):
        """
        Raises AlreadyExistsException with status code `409` if `val` evaluates to `False`

        Default message format is: `resource_name` with `field_name` '`field_value`' already exists.
        """

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        cls.raise_if(
            val=not val,
            resource_name=resource_name,
            field_value=field_value,
            field_name=field_name,
            msg=msg,
        )


class ValidationException(BusinessLogicException):
    """
    An exception raised when a submitted form or document did not pass validation.
    """
