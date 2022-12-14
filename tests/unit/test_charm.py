# Copyright 2022 Niels Robin-Aubertin
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import MagicMock, patch

import ops.testing
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus, Container
from ops.testing import Harness

from charm import SearxngK8SCharm


class MockExecProcess(object):
    wait_output = MagicMock(return_value=("", None))


class TestCharm(unittest.TestCase):
    def setUp(self):
        # Enable more accurate simulation of container networking.
        # For more information, see https://juju.is/docs/sdk/testing#heading--simulate-can-connect
        ops.testing.SIMULATE_CAN_CONNECT = True
        self.addCleanup(setattr, ops.testing, "SIMULATE_CAN_CONNECT", False)

        self.harness = Harness(SearxngK8SCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_searxng_pebble_ready(self):
        # Simulate the container coming up and emission of pebble-ready event
        self.harness.container_pebble_ready("searxng")
        # Check we've got the plan we expected
        self.assertEqual(
            self.harness.get_container_pebble_plan("searxng").to_dict(),
            {
                "services": {
                    "searxng": {
                        "override": "replace",
                        "summary": "searxng",
                        "command": "/usr/local/searxng/dockerfiles/docker-entrypoint.sh",
                        "startup": "enabled",
                        "environment": {
                            "AUTOCOMPLETE": "",
                            "INSTANCE_NAME": "searxng",
                        },
                    }
                },
            }
        )
        # Check the service was started
        service = self.harness.model.unit.get_container("searxng").get_service("searxng")
        self.assertTrue(service.is_running())
        # Ensure we set an ActiveStatus with no message
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    def test_config_changed_valid_can_connect(self):
        with patch.object(Container, "exec", return_value=MockExecProcess()):
            # Ensure the simulated Pebble API is reachable
            self.harness.set_can_connect("searxng", True)
            # start the container (increases coverage)
            container = self.harness.model.unit.get_container("searxng")
            # Trigger a config-changed event with an updated value
            self.harness.update_config({"instance-name": "foo"})
            # Get the plan now we've run PebbleReady
            updated_plan = self.harness.get_container_pebble_plan("searxng").to_dict()
            updated_env = updated_plan["services"]["searxng"]["environment"]
            # Check the config change was effective
            self.assertEqual(
                updated_env,
                {
                    "AUTOCOMPLETE": "",
                    "INSTANCE_NAME": "foo",
                },
            )
            self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    def test_config_changed_valid_cannot_connect(self):
        with patch.object(Container, "exec", return_value=MockExecProcess()):

            container = self.harness.model.unit.get_container("searxng")
            with patch.object(container, "can_connect", MagicMock(return_value=False)):
                # Ensure the simulated Pebble API is reachable
                self.harness.set_can_connect("searxng", True)

                # Trigger a config-changed event with an updated value
                self.harness.update_config({"instance-name": "foo"})

                # Check the charm is in WaitingStatus
                self.assertIsInstance(self.harness.model.unit.status, WaitingStatus)

    def test_config_changed_invalid(self):
        # Ensure the simulated Pebble API is reachable
        self.harness.set_can_connect("searxng", True)
        # Trigger a config-changed event with an updated value
        self.harness.update_config({"autocomplete": "foobar"})
        # Check the charm is in BlockedStatus
        self.assertIsInstance(self.harness.model.unit.status, BlockedStatus)
