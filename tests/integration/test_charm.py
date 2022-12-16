#!/usr/bin/env python3
# Copyright 2022 Niels Robin-Aubertin
# See LICENSE file for licensing details.

import asyncio
import logging
from pathlib import Path

import pytest
import yaml
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.fixture
def metadata():
    return yaml.safe_load(Path("./metadata.yaml").read_text())


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest, metadata):
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    # Build and deploy charm from local source folder
    charm = await ops_test.build_charm(".")
    resources = {
        "searxng-image": metadata["resources"]["searxng-image"]["upstream-source"]
    }

    # Deploy the charm and wait for active/idle status
    await asyncio.gather(
        ops_test.model.deploy(
            charm, resources=resources, application_name=metadata["name"], series="jammy"
        ),
        ops_test.model.wait_for_idle(
            apps=[metadata["name"]], status="active", raise_on_blocked=True, timeout=1000
        ),
    )
