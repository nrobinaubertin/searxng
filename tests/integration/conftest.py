#!/usr/bin/env python3
# Copyright 2022 Niels Robin-Aubertin
# See LICENSE file for licensing details.

from pathlib import Path

import pytest
import pytest_asyncio
import yaml
from ops.model import Application
from pytest_operator.plugin import OpsTest


@pytest.fixture(scope="module")
def metadata():
    return yaml.safe_load(Path("./metadata.yaml").read_text())


@pytest_asyncio.fixture(scope="module")
async def app(ops_test: OpsTest, metadata):
    """
    Builds the charm and deploys it
    """
    # Build and deploy ingress
    charm = await ops_test.build_charm(".")
    resources = {"searxng-image": metadata["resources"]["searxng-image"]["upstream-source"]}

    application: Application = await ops_test.model.deploy(
        charm, resources=resources, application_name=metadata["name"], series="jammy"
    )

    await ops_test.model.wait_for_idle(
        apps=[metadata["name"]], status="active", raise_on_blocked=True, timeout=1000
    )

    yield application
