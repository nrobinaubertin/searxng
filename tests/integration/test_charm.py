#!/usr/bin/env python3
# Copyright 2022 Niels Robin-Aubertin
# See LICENSE file for licensing details.

import logging

import pytest
import requests
from ops.model import ActiveStatus, Application
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_service_reachable(ops_test: OpsTest, app: Application):
    """Check that the starting page is reachable.
    Assume that the charm has already been built and is running.
    """
    assert app.units[0].workload_status == ActiveStatus.name
    assert ops_test.model
    status = await ops_test.model.get_status()
    unit = list(status.applications[app.name].units)[0]
    address = status["applications"][app.name]["units"][unit]["address"]
    response = requests.get(f"http://{address}:8080")
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_instance_name_change(ops_test: OpsTest, app: Application):
    """Check that the starting page is reachable.
    Assume that the charm has already been built and is running.
    """
    assert ops_test.model
    application = ops_test.model.applications[app.name]

    await application.set_config({"instance-name": "foobar"})
    await ops_test.model.wait_for_idle(status=ActiveStatus.name)
    assert application.status == ActiveStatus.name

    status = await ops_test.model.get_status()
    unit = list(status.applications[app.name].units)[0]
    address = status["applications"][app.name]["units"][unit]["address"]
    response = requests.get(f"http://{address}:8080")

    assert response.status_code == 200
    assert "<title>foobar</title>" in response.text
