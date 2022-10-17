#!/usr/bin/env python
# encoding: utf-8

"""PipelineStep"""

from .event import Event


class PipelineStep:
    """A pipeline or workflow is made of (pipeline) steps. This
    is the base class for all steps."""

    def __init__(self, proc, name: str):
        self.processor = proc
        self.step_name = name

    @property
    def step_data(self):
        """Every pipeline step has personal data"""
        return self.processor.data[self.step_name]

    @step_data.setter
    def step_data(self, value):
        """Every pipeline step has personal data"""
        self.processor.data[self.step_name] = value

    def initialize(self):
        """Will be invoked during the pipeline start-up.

        Some steps may only subclass this method, e.g. to load (manual) data,
        which are needed in subsequent steps.
        """

    def finalize(self):
        """Will be invoked when all events have been processed and the
        pipeline shuts down."""

    def main(self, event: Event):
        """Invoked for every event, this is where usally event processing
        takes place

        If main() returns True, then the event will be filtered out, and
        all remaining steps will be skipped.
        """

    def on_new_event_file(self, data, file):
        """For some steps it is relevant to know, whether processing a
        new event file has started."""
