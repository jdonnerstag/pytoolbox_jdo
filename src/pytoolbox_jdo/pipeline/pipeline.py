#!/usr/bin/env python
# encoding: utf-8

"""Pipeline"""

import os
import time
import uuid
from typing import Any, Type
from contextlib import ContextDecorator
from pathlib import Path

from .. import logging
from .. import import_module_from_file
from .pipeline_step import PipelineStep
from .event import Event

logger = logging.get_logger(__name__, logging.DEBUG)


class PipelineException(Exception):
    """PipelineException"""


class Pipeline(ContextDecorator):
    """This is the pipeline, including mechanics to import pipeline
    steps, initialize and shut them down, and invoke the steps in the
    defined sequence to process events."""

    def __init__(self, step_class: Type, step_dir: None | Path):
        """Constructor"""
        super().__init__()

        self.step_class = step_class

        # Often pipelines are just a sequence of steps, but many times
        # it improves overall structure and readability, if pipeline steps can be
        # grouped and assigned assigned a name; think functions and function calls.
        # This is what `pipelines` is about: <group> -> [list of pipeline steps].
        self.pipelines: dict[str, list[PipelineStep]] = {}

        # Most steps require some reference data. The step itself is responsible
        # to load it. The step is also responsible to register its data here, so
        # that it can be leveraged in later steps.
        self.data: dict[str, Any] = {}

        # Number of events processed
        self.event_count = 0

        self.start_time: float = 0

        if step_dir:
            if step_dir.is_dir():
                self.load_pipeline(step_dir)
            else:
                raise PipelineException(f"Not a directory: {step_dir}")

    def add_pipeline(self, name: str):
        """Add a new pipeline (group of steps)"""
        self.pipelines.setdefault(name, [])

    def add_step(self, name: str, step: PipelineStep):
        """Add the step to an already registered pipeline"""
        assert isinstance(step, self.step_class)
        self.pipelines[name].append(step)

    def load_step(self, file: Path):
        """Load a PipelineStep from a file"""

        mod = import_module_from_file(file)

        # If both a file <name>.py and a directory <name> exist, then python will use the
        # directory (package), which is not what we want. Hence: raise an exception
        if mod.__package__ and (mod.__name__ == mod.__package__.split(".")[-1]):
            raise PipelineException(
                "Directory and file have the same name, except for the extension. "
                + "Please rename either: %s",
                file,
            )

        # Make sure the module has a variable called ...
        if "STEP" not in dir(mod):
            raise PipelineException(f"Missing 'STEP' variable in '{file}'")

        # Create an entry for the steps in a package if it doesn't exist yet
        pipe_name = mod.__package__ or ""
        self.add_pipeline(pipe_name)

        if not issubclass(mod.STEP, self.step_class):
            raise PipelineException(
                f"STEP objects must of type {self.step_class.__name__}: '{file}'"
            )

        # Call the constructor of the step
        try:
            obj = mod.STEP(self, mod.__name__)
            self.add_step(pipe_name, obj)
        except BaseException as ex:
            raise PipelineException(
                f"Failed to instantiate pipeline step: {file}"
            ) from ex

    def load_pipeline(self, path: Path):
        """Load all files (python modules) from the directory specified (recursive).

        Each directory is a python package and access to the python modules will be
        possible the python way.
        """
        assert path.is_dir(), f"Not a directory: {path}"

        logger.info("Load pipeline steps from '%s'", path)
        if not path or not os.path.isdir(path):
            raise PipelineException(f"Path is not a directory: {path}")

        count = 0
        pipeline = {}
        for file in path.glob("**/*.py"):
            if file.name and file.name[0].isalnum():
                self.load_step(file)
                count += 1
            else:
                logger.debug("Pipeline file ignored: %s", file)

        logger.info("Loaded %d pipelines and %d steps", len(pipeline), count)
        return self

    def foreach_step(self):
        """Loop over all Steps"""

        for k, pipe in self.pipelines.items():
            for step in pipe:
                try:
                    yield step
                except BaseException as ex:
                    raise PipelineException(
                        f"Error while executing pipeline={k}, step='{step.step_name}'"
                    ) from ex

    def initialize(self):
        """Each step is an object of type PipelineStep, which has an initialize function.
        Iterate through all steps and invoke the initialize function. Typically
        the reference data are loaded by each step.
        """

        self.start_time = time.time()
        logger.info("Initialize every pipeline step")

        for step in self.foreach_step():
            step.initialize()

        logger.info("Time spent to initialize: %s", self.elapsed(self.start_time))

    def finalize_steps(self):
        """Allow every step to clean up, when all events have been processed"""

        start_time = time.time()
        logger.info("Cleanup every pipeline step")

        for step in self.foreach_step():
            step.finalize()

        logger.info("Time spent on finalization: %s", self.elapsed(start_time))

    def on_new_event_file(self, data, file: Path):
        """Start processing a new event file.

        Allow every step to pre-process the whole file ahead of each individual event.
        """

        start_time = time.time()
        logger.info("New event file received: %s", file)

        for step in self.foreach_step():
            step.on_new_event_file(data, file)

        logger.info(
            "Finished new-event-file received: %s in %s", file, self.elapsed(start_time)
        )

    def exec_step(self, _pipeline: str, step: PipelineStep, event: Event):
        """Possibly be subclassed, this function invokes a step to process the event"""
        return step.main(event)

    def _exec_pipeline(self, pipeline: str, event):
        """Execute a specific pipeline"""

        # logger.debug("Launch pipeline: '%s'", name)

        pipe = self.pipelines[pipeline]
        for step in pipe:
            try:
                # logger.debug(f"Execute pipeline: {name}.{step.step_name}")
                event.trace(step.step_name, "enter")
                if self.exec_step(pipeline, step, event) is True:
                    break
            except BaseException as ex:
                raise PipelineException(
                    f"Error while executing step={step.step_name}"
                ) from ex

        # logger.debug("Finished with pipeline: '%s'", name)

    def process_event(self, pipeline: str, event: Event):
        """Execute the pipeline for event"""
        assert isinstance(event, Event)

        self.event_count += 1
        event.meta["event_count"] = self.event_count
        event.meta["time_start"] = time.time()

        # Create a random unique user id for this event.
        # Some commission systems require a stable commission-ID, e.g. to support
        # deletions of previously calculated commissions. The ID serves the
        # purpose to identify these commissions. Pipeline steps may replace it
        # with a more readable id, or one that is compliant with the target system.
        event.meta["uuid"] = str(uuid.uuid4())

        # logger.debug(f"Start processing event: {self.event_count}")

        try:
            self._exec_pipeline(pipeline, event)
        except BaseException as ex:
            raise PipelineException(
                f"Error while executing pipeline '{pipeline}'"
            ) from ex

        event.meta["time_finished"] = time.time()
        # print(event)
        # logger.debug(f"Finished processing event: {self.event_count}")

        return self

    @classmethod
    def elapsed(cls, start_time: float):
        """Determine the elapsed time in %02d:%02:%02d format"""

        elapsed = round(time.time() - start_time)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    def __enter__(self):
        self.initialize()
        self.finalize_steps()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type:
            elapsed = self.elapsed(self.start_time)
            logger.info(
                "Processed %d events in %s elapsed time", self.event_count, elapsed
            )

            # Allow the steps to do post-processing activities
            self.finalize_steps()

            elapsed = self.elapsed(self.start_time)
            logger.info("Finished job in %s secs", elapsed)
        else:
            logger.error("Caught exception during pipeline execution: ...")
            data = [exc_value]
            exc_value = exc_value.__cause__
            while exc_value:
                data.append(exc_value)
                exc_value = exc_value.__cause__

            for msg in data:
                logger.error(".. %s", msg)

        return False
