#!/usr/bin/env python3
# Copyright 2021 Fran
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

import ops
from oci_image import OCIImageResource, OCIImageResourceError
from ops.framework import StoredState
from ops.charm import CharmBase
from ops.main import main
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
)


logger = logging.getLogger(__name__)


class HelloWorldCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.image = OCIImageResource(self, "site-image")

        self.framework.observe(self.on.start, self._configure_pod)
        self.framework.observe(self.on.config_changed, self._configure_pod)
        self.framework.observe(self.on.leader_elected, self._configure_pod)
        self.framework.observe(self.on.upgrade_charm, self._configure_pod)

        self._stored.set_default(things=[])

    def _make_k8s_ingress(self) -> list:
        """Return an ingress that you can use in k8s_resources

        :returns: A list to be used as k8s ingress
        """

        hostname = self.model.config["hostname"]

        ingress = {
            "name": "{}-ingress".format(self.app.name),
            "spec": {
                "rules": [
                    {
                        "host": hostname,
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "backend": {
                                        "serviceName": self.app.name,
                                        "servicePort": 80,
                                    },
                                }
                            ]
                        },
                    }
                ]
            },
            "annotations": {
                "nginx.ingress.kubernetes.io/ssl-redirect": "false",
            },
        }

        return [ingress]

    def _make_pod_spec(self) -> dict:
        """Return a pod spec with some core configuration.

        :returns: A pod spec
        """

        try:
            image_details = self.image.fetch()
            logging.info("using imageDetails: {}")
        except OCIImageResourceError:
            logging.exception(
                "An error occurred while fetching the image info"
            )
            self.unit.status = BlockedStatus(
                "Error fetching image information"
            )
            return {}

        return {
            "version": 3,  # otherwise resources are ignored
            "containers": [
                {
                    "name": self.app.name,
                    "imageDetails": image_details,
                    "imagePullPolicy": "Always",
                    "ports": [{"containerPort": 80, "protocol": "TCP"}],
                    "kubernetes": {
                        "readinessProbe": {
                            "httpGet": {"path": "/", "port": 80}
                        },
                    },
                }
            ],
        }

    def _configure_pod(self, event: ops.framework.EventBase) -> None:
        """Assemble the pod spec and apply it, if possible.

        :param event: Event that triggered the method.
        """
        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return

        self.unit.status = MaintenanceStatus("Assembling pod spec")

        pod_spec = self._make_pod_spec()
        resources = pod_spec.get("kubernetesResources", {})
        resources["ingressResources"] = self._make_k8s_ingress()

        self.unit.status = MaintenanceStatus("Setting pod spec")
        self.model.pod.set_spec(
            pod_spec, k8s_resources={"kubernetesResources": resources}
        )
        logger.info("Setting active status")
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(HelloWorldCharm)
