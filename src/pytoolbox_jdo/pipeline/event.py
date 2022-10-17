#!/usr/bin/env python
# encoding: utf-8

"""Event"""

from pytoolbox_jdo import dict_utils as du


class Event(dict):
    """A generic event.

    Basically a dict, it is able to hold any data, and able to
    be updated in every pipeline step.
    """

    def __init__(self, **kvargs):
        super().__init__(**kvargs)

    @property
    def meta(self) -> dict:
        """Every event has meta-data, maintained in the 'meta' attribute"""
        return self.setdefault("_meta_", {})

    def deep_get(self, *args, **kvargs):
        """Get event data identified by their access-path, possibly deep."""
        return du.deep_get(self, *args, **kvargs)

    def deep_set(self, *args, **kvargs):
        """Update/set event data identified by their access-path, possibly deep."""
        return du.deep_set(self, *args, **kvargs)

    def deep_delete(self, *args, **kvargs):
        """Delete event data identified by their access-path, possibly deep."""
        return du.deep_delete(self, *args, **kvargs)

    def trace(self, name, msg):
        """Every event has a 'trace' attribute, which helps (users) to
        understand what happened"""

        data = self.setdefault("_trace_", [])
        data.append((name, msg))

    @property
    def uuid(self):
        """Get the UUID assigned to the event."""
        return self.meta["uuid"]
