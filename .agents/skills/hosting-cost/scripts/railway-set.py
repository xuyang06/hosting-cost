#!/usr/bin/env python3
"""Change one Railway service's cost-relevant settings, by name, dry-run first.

  railway-set.py PROJECT ENV SERVICE [--start-command CMD] [--image IMG] [--sleep on|off]
  railway-set.py myapp production web --sleep on            # shows the diff only
  railway-set.py myapp production web --sleep on --apply    # writes and redeploys

Resolves names to IDs itself and refuses anything ambiguous, so a production
service is never changed through a mistyped ID. With --apply it updates the
service instance, then redeploys it so the change takes effect. The API answers
`true` as soon as the request is accepted; that is not proof the new settings
are running. Verify afterwards (see the skill's "Verify" step).
"""
import argparse
import importlib.util
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("usage", os.path.join(_here, "railway-usage.py"))
usage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(usage)

UPDATE = """mutation($s:String!,$e:String!,$i:ServiceInstanceUpdateInput!){
  serviceInstanceUpdate(serviceId:$s, environmentId:$e, input:$i) }"""
REDEPLOY = """mutation($s:String!,$e:String!){ serviceInstanceRedeploy(serviceId:$s, environmentId:$e) }"""


def find(project: str, env: str, service: str) -> dict:
    hits = []
    for ws in usage.gql(usage.PROJECTS, {})["me"]["workspaces"]:
        for p in ws["projects"]["edges"]:
            p = p["node"]
            if p["name"] != project:
                continue
            for e in p["environments"]["edges"]:
                e = e["node"]
                if e["name"] != env:
                    continue
                for si in e["serviceInstances"]["edges"]:
                    si = si["node"]
                    if si["serviceName"] == service:
                        hits.append({**si, "environmentId": e["id"]})
    if len(hits) != 1:
        sys.exit(f"Expected exactly one {project}/{env}/{service}, found {len(hits)}. "
                 "Check names with railway-usage.py.")
    return hits[0]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("environment")
    ap.add_argument("service")
    ap.add_argument("--start-command")
    ap.add_argument("--image", help="pin an exact tag, e.g. mysql:9.7.4, never a floating one")
    ap.add_argument("--sleep", choices=["on", "off"])
    ap.add_argument("--apply", action="store_true", help="write the change and redeploy (default: dry run)")
    a = ap.parse_args()

    si = find(a.project, a.environment, a.service)
    change, show = {}, []
    if a.start_command is not None:
        change["startCommand"] = a.start_command
        show.append(("startCommand", si["startCommand"], a.start_command))
    if a.image is not None:
        change["source"] = {"image": a.image}
        show.append(("image", (si["source"] or {}).get("image"), a.image))
    if a.sleep is not None:
        change["sleepApplication"] = a.sleep == "on"
        show.append(("sleepApplication", si["sleepApplication"], a.sleep == "on"))
    if not change:
        sys.exit("Nothing to change. Pass --start-command, --image or --sleep.")

    print(f"{a.project}/{a.environment}/{a.service}")
    for k, before, after in show:
        print(f"  {k}:\n    before: {before}\n    after:  {after}")
    if not a.apply:
        print("\nDry run. Re-run with --apply to write and redeploy.")
        return
    usage.gql(UPDATE, {"s": si["serviceId"], "e": si["environmentId"], "i": change})
    usage.gql(REDEPLOY, {"s": si["serviceId"], "e": si["environmentId"]})
    print("\nUpdated and redeploy requested. Not yet verified: check the running process, health and logs.")


if __name__ == "__main__":
    main()
