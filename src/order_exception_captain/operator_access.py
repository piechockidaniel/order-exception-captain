"""Small, explicit access boundary for a non-local operator desk."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from hmac import compare_digest
from ipaddress import ip_address
from typing import Mapping


class OperatorAccessConfigurationError(ValueError):
    """Raised when the operator access configuration is unsafe or incomplete."""


@dataclass(frozen=True)
class OperatorAccess:
    """An optional bearer-token gate whose secret is never logged or serialised."""

    token: str | None = field(default=None, repr=False)

    @property
    def is_enabled(self) -> bool:
        return self.token is not None

    @classmethod
    def from_token(cls, token: str | None) -> "OperatorAccess":
        normalised = (token or "").strip()
        if not normalised:
            return cls()
        if len(normalised) < 16:
            raise OperatorAccessConfigurationError("OEC_OPERATOR_TOKEN must contain at least 16 characters.")
        return cls(token=normalised)

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "OperatorAccess":
        values = os.environ if environment is None else environment
        return cls.from_token(values.get("OEC_OPERATOR_TOKEN"))

    def authorizes(self, authorization_header: str | None) -> bool:
        """Use a constant-time comparison without disclosing whether a token was close."""
        if not self.is_enabled:
            return True
        if authorization_header is None:
            return False
        scheme, separator, presented_token = authorization_header.partition(" ")
        return bool(separator) and scheme.lower() == "bearer" and compare_digest(presented_token, self.token or "")


@dataclass(frozen=True)
class AdminAccess:
    """Separate configuration authority; an operator token alone can never publish policy."""

    token: str | None = field(default=None, repr=False)

    @property
    def is_enabled(self) -> bool:
        return self.token is not None

    @classmethod
    def from_token(cls, token: str | None) -> "AdminAccess":
        normalised = (token or "").strip()
        if not normalised:
            return cls()
        if len(normalised) < 16:
            raise OperatorAccessConfigurationError("OEC_ADMIN_TOKEN must contain at least 16 characters.")
        return cls(token=normalised)

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "AdminAccess":
        values = os.environ if environment is None else environment
        return cls.from_token(values.get("OEC_ADMIN_TOKEN"))

    def authorizes(self, presented_token: str | None) -> bool:
        if not self.is_enabled or presented_token is None:
            return False
        return compare_digest(presented_token.strip(), self.token or "")


def is_loopback_host(host: str) -> bool:
    """Return true for an IPv4/IPv6 loopback address or localhost."""
    normalised = host.strip().lower()
    if normalised == "localhost":
        return True
    try:
        return ip_address(normalised).is_loopback
    except ValueError:
        return False


def require_access_for_host(host: str, access: OperatorAccess) -> None:
    """Reject accidental exposure when no operator access token was configured."""
    if not is_loopback_host(host) and not access.is_enabled:
        raise OperatorAccessConfigurationError(
            "A non-local host requires OEC_OPERATOR_TOKEN; keep the default loopback host for an open local demo."
        )
