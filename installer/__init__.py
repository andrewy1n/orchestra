"""Provider-matrix installer for orchestra host payloads.

The package is checkout-side: ``orchestra install`` imports it lazily so a
pip-installed CLI still answers ``--help`` and the non-install subcommands
without the repository root present.
"""

from installer.model import Provider

__all__ = ["Provider"]
