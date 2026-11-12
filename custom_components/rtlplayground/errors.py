"""Exceptions raised by the RTLPlayground client."""


class RtlPlaygroundError(Exception):
    """Base error for the RTLPlayground integration."""


class CannotConnect(RtlPlaygroundError):
    """The switch did not answer (network down, wrong address, timeout)."""


class InvalidAuth(RtlPlaygroundError):
    """The password was rejected, or a fresh login was refused."""


class ApiError(RtlPlaygroundError):
    """The switch answered, but not with what the API documents."""
