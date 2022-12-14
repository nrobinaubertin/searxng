#!/usr/bin/env python3
# Copyright 2022 Niels Robin-Aubertin
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus
from ops.pebble import ExecError

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

VALID_AUTOCOMPLETE_BACKENDS = ["", "dbpedia", "duckduckgo", "google", "startpage", "swisscows", "qwant", "wikipedia"]


class SearxngK8SCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.searxng_pebble_ready, self._on_searxng_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_searxng_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.

        Change this example to suit your needs. You'll need to specify the right entrypoint and
        environment configuration for your specific workload.

        Learn more about interacting with Pebble at at https://juju.is/docs/sdk/pebble.
        """
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Add initial Pebble config layer using the Pebble API
        container.add_layer("searxng", self._pebble_layer, combine=True)
        # Make Pebble reevaluate its plan, ensuring any services are started if enabled.
        container.replan()
        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, event):
        """Handle changed configuration.

        Change this example to suit your needs. If you don't need to handle config, you can remove
        this method.

        Learn more about config at https://juju.is/docs/sdk/config
        """

        container = self.unit.get_container("searxng")
        services = container.get_plan().to_dict().get("services", {})

        # Fetch the new config value
        autocomplete = self.model.config["autocomplete"].lower()

        if autocomplete not in VALID_AUTOCOMPLETE_BACKENDS:
            # In this case, the config option is bad, so block the charm and notify the operator.
            self.unit.status = BlockedStatus("invalid autocomplete backend: '{autocomplete}'")
            return

        if services != self._pebble_layer["services"]:
            if not container.can_connect():
                # We were unable to connect to the Pebble API, so we defer this event
                event.defer()
                self.unit.status = WaitingStatus("waiting for Pebble API")
                return

            container.add_layer("searxng", self._pebble_layer, combine=True)
            container.replan()
            logging.info("Added updated layer 'searxng' to Pebble plan")

            # change settings file inside the container
            try:
                container.exec(
                    ["sed", "-i", "-e",
                        f's/instance_name: "[^"]*"/instance_name: "{self.model.config["instance-name"]}"/',
                        "/etc/searxng/settings.yml"]
                ).wait_output()
                container.exec(
                    ["sed", "-i", "-e",
                        f's/autocomplete: "[^"]*"/autocomplete: "{self.model.config["autocomplete"]}"/',
                        "/etc/searxng/settings.yml"]
                ).wait_output()
            except ExecError as ex:
                logging.debug(ex)

            if container.get_service("searxng").is_running():
                container.stop("searxng")

            container.start("searxng")
            logging.info("Restarted searxng service")
            if self.unit.get_container("searxng").can_connect():
                self.unit.status = ActiveStatus()

    @property
    def _pebble_layer(self):
        """Return a dictionary representing a Pebble layer."""
        return {
            "summary": "searxng layer",
            "description": "pebble config layer for searxng",
            "services": {
                "searxng": {
                    "override": "replace",
                    "summary": "searxng",
                    "command": "/usr/local/searxng/dockerfiles/docker-entrypoint.sh",
                    "startup": "enabled",
                    "environment": {
                        "AUTOCOMPLETE": str(self.model.config['autocomplete']),
                        "INSTANCE_NAME": str(self.model.config['instance-name']),
                    },
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    main(SearxngK8SCharm)
