#!/usr/bin/env bash
# Pinned component versions for the public NetBox demo deployment.
#
# Bump these deliberately (open a PR) when you want to upgrade — the
# deploy pipeline never resolves "latest" on its own, so a new upstream
# release can never silently break the running instance.
#
# Current tag list: https://hub.docker.com/r/netboxcommunity/netbox/tags

# netboxcommunity/netbox image tag: "<netbox-version>-<netbox-docker-build>"
export NETBOX_VERSION="v4.6.8-5.0.2"
export NETBOX_PKI_PLUGIN_VERSION="0.1.0"
