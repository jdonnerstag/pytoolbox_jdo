#!/usr/bin/env python
# encoding: utf-8

"""Pipeline or workflow

A pipeline consists of steps, and in our implementation each step is defined
in a separate python file. The filenames determines the sequence (ASCII sort order).
Using a number (e.g. 0100-) to start the filename is usually a good idea.
You can group steps into subdirectories. The subdirs should follow a similar
naming convention. The subflows must be explicitly invoked. This can also be
used to execute alternate flows, e.g. business unit DIRECT or INDIRECT flows.
Most steps require some of (external) data, to filter, lookup, enrich, the
event.
The event is pretty much just a dict (json) that can arbitrarily be modified
and enriched by ever step. The event is passed to the steps in the sequence
defined.
"""

from .event import Event
from .pipeline_step import PipelineStep
from .pipeline import Pipeline
