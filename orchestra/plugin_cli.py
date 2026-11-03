from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from orchestra.canon.extensions import PLUGIN_GROUPS, list_plugins


def add_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    plugins = sub.add_parser("plugins", help="List installed plugins")
    actions = plugins.add_subparsers(dest="action", required=True)
    listing = actions.add_parser("list", help="List installed plugins by scope")
    listing.add_argument("--scope", choices=tuple(PLUGIN_GROUPS), default=None)
    listing.add_argument("--format", choices=("table", "json"), default="table")


def run(args: argparse.Namespace) -> int:
    descriptors = sorted(list_plugins(args.scope), key=lambda item: (item.scope, item.plugin_id))
    if args.format == "json":
        print(json.dumps([asdict(item) for item in descriptors], sort_keys=True))
        return 0
    print("scope\tid\tapi\tdistribution\tversion\ttarget")
    for descriptor in descriptors:
        print(
            "\t".join(
                (
                    descriptor.scope,
                    descriptor.plugin_id,
                    descriptor.api_version,
                    descriptor.distribution,
                    descriptor.version,
                    descriptor.target,
                )
            )
        )
    return 0
