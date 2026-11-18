#!/usr/bin/env python3
"""Rank every Railway service on the account by what it costs to keep running.

Read-only. Prints, per project/environment/service: average and peak memory,
average vCPU, an estimated $/month, and the settings that usually explain a
high number (start command, image, sleep flag, replicas).

  railway-usage.py                  # all projects, last 7 days
  railway-usage.py --days 30        # longer window
  railway-usage.py --project NAME   # one project
  railway-usage.py --json           # machine-readable

Auth: the Railway CLI's session (`railway login`) from ~/.railway/config.json,
or RAILWAY_API_TOKEN. Prices default to Railway's list prices; override with
--mem-price / --cpu-price ($ per GB-month / per vCPU-month) to match a receipt.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://backboard.railway.com/graphql/v2"
MINUTES_PER_MONTH = 43_200


def token() -> str:
    if os.environ.get("RAILWAY_API_TOKEN"):
        return os.environ["RAILWAY_API_TOKEN"]
    path = os.path.expanduser("~/.railway/config.json")
    try:
        user = json.load(open(path)).get("user") or {}
    except FileNotFoundError:
        sys.exit("No Railway session. Run `railway login` (or set RAILWAY_API_TOKEN).")
    tok = user.get("accessToken") or user.get("token")
    if not tok:
        sys.exit("No token in ~/.railway/config.json. Run `railway login`.")
    return tok


def gql(query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        API,
        json.dumps({"query": query, "variables": variables}).encode(),
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token(),
            # Without a User-Agent, Cloudflare in front of the API answers 403,
            # which reads like a permissions problem and is not one.
            "User-Agent": "hosting-cost-skill",
        },
    )
    try:
        body = json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        hint = " Session expired? Run `railway login`." if e.code in (401, 403) else ""
        sys.exit(f"Railway API HTTP {e.code}.{hint}")
    if body.get("errors"):
        msg = body["errors"][0].get("message", "")
        hint = " Run `railway login`." if "auth" in msg.lower() else ""
        sys.exit(f"Railway API error: {msg}.{hint}")
    return body["data"]


PROJECTS = """{ me { workspaces { projects { edges { node { id name
  environments { edges { node { id name serviceInstances { edges { node {
    serviceId serviceName startCommand numReplicas sleepApplication source { image repo } } } } } } }
} } } } } }"""

METRICS = """query($e:String!,$s:String!,$t:DateTime!){ metrics(environmentId:$e, serviceId:$s,
  startDate:$t, measurements:[MEMORY_USAGE_GB, CPU_USAGE], sampleRateSeconds:3600){
  measurement values{ value } } }"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--project", help="only this project (exact name)")
    ap.add_argument("--mem-price", type=float, default=10.0, help="$ per GB-month (default 10)")
    ap.add_argument("--cpu-price", type=float, default=20.0, help="$ per vCPU-month (default 20)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    start = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=a.days)).isoformat()
    rows = []
    for ws in gql(PROJECTS, {})["me"]["workspaces"]:
        for p in ws["projects"]["edges"]:
            p = p["node"]
            if a.project and p["name"] != a.project:
                continue
            for e in p["environments"]["edges"]:
                e = e["node"]
                for si in e["serviceInstances"]["edges"]:
                    si = si["node"]
                    m = gql(METRICS, {"e": e["id"], "s": si["serviceId"], "t": start})["metrics"]
                    series = {x["measurement"]: [v["value"] for v in x["values"]] for x in m}
                    mem, cpu = series.get("MEMORY_USAGE_GB", []), series.get("CPU_USAGE", [])
                    mem_gb = sum(mem) / len(mem) if mem else 0.0
                    cpu_avg = sum(cpu) / len(cpu) if cpu else 0.0
                    rows.append({
                        "project": p["name"], "environment": e["name"], "service": si["serviceName"],
                        "projectId": p["id"], "environmentId": e["id"], "serviceId": si["serviceId"],
                        "mem_mb": round(mem_gb * 1024), "mem_peak_mb": round(max(mem) * 1024) if mem else 0,
                        "vcpu": round(cpu_avg, 4),
                        "usd_month": round(mem_gb * a.mem_price + cpu_avg * a.cpu_price, 2),
                        "sleep": si["sleepApplication"], "replicas": si["numReplicas"],
                        "image": (si["source"] or {}).get("image"), "repo": (si["source"] or {}).get("repo"),
                        "startCommand": si["startCommand"],
                    })
    rows.sort(key=lambda r: r["usd_month"], reverse=True)
    if a.json:
        print(json.dumps(rows, indent=1))
        return
    total = sum(r["usd_month"] for r in rows) or 1
    print(f"{'project':<18}{'env':<12}{'service':<12}{'avg MB':>7}{'peak':>7}{'vCPU':>8}{'$/mo':>7}{'share':>6}  sleep  source")
    for r in rows:
        src = r["image"] or r["repo"] or "-"
        print(f"{r['project'][:17]:<18}{r['environment'][:11]:<12}{r['service'][:11]:<12}{r['mem_mb']:>7}"
              f"{r['mem_peak_mb']:>7}{r['vcpu']:>8.3f}{r['usd_month']:>7.2f}{r['usd_month']/total*100:>5.0f}%"
              f"  {str(r['sleep'] or False):<6} {src}")
        if r["startCommand"]:
            print(f"{'':<42}start: {r['startCommand'][:110]}")
    print(f"\nTOTAL ~${sum(r['usd_month'] for r in rows):.2f}/month over the last {a.days} days "
          f"(memory ${a.mem_price}/GB-mo, CPU ${a.cpu_price}/vCPU-mo; excludes disk, network and plan fee)")


if __name__ == "__main__":
    main()
