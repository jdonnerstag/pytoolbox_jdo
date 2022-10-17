#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=missing-function-docstring, missing-module-docstring

from pathlib import Path

import pytest

from pytoolbox_jdo.pipeline import Event, PipelineStep, Pipeline


data_dir = Path(__file__).parent / "data"


def test_constructor():
    pipe = Pipeline(step_class=PipelineStep, step_dir=None)
    step = PipelineStep(pipe, "test-1")
    event = Event()

    assert "_meta_" not in event
    _ = event.meta
    assert "_meta_" in event

    with pytest.raises(Exception):
        pipe.add_step("", step)

    pipe.add_pipeline("")
    pipe.add_step("", step)

    step2 = PipelineStep(pipe, "test-2")
    pipe.add_step("", step2)

    pipe.initialize()
    pipe.finalize_steps()
    pipe.on_new_event_file(bytes(), data_dir / "test.dat")
    pipe.process_event("", event)

    with pipe:
        pass
