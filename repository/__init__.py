"""
Wrappers around all the nasty little things that need to be done outside of a service
that either have side-effects or raise exceptions that would prevent them from being
unit tested.
"""

from . import shell
