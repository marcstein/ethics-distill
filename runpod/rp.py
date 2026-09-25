#!/usr/bin/env python3
"""Minimal RunPod control for ethics-distill (GraphQL). Never touches volumes or pods it did not create (name prefix 'ed-').
  rp.py volume            create/show the ethics-distill network volume
  rp.py up GPU [NAME]     deploy a pod on the volume (GPU e.g. "NVIDIA H200", "NVIDIA RTX A5000")
  rp.py ssh               print ssh target(s) for running ed- pods
  rp.py down [ID]         terminate ed- pods (the volume persists)
  rp.py status            balance, spend, our pods"""
import json, os, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = [l.split("=", 1)[1].strip() for l in open(os.path.join(ROOT, ".env")) if l.startswith("RUNPOD_API_KEY=")][0]
DC = "US-CA-2"; VOL = "ed-ethics-distill-vol"; IMAGE = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"  # RunPod official torch 2.8 template image, widely cached
PUB = "\n".join(open(os.path.expanduser(p)).read().strip() for p in ["~/.ssh/id_ed25519.pub"] if os.path.exists(os.path.expanduser(p)))
def gql(q, v=None):
    r = urllib.request.Request("https://api.runpod.io/graphql", data=json.dumps({"query": q, "variables": v or {}}).encode(),
                               headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json", "User-Agent": "ethics-distill"})
    d = json.loads(urllib.request.urlopen(r, timeout=60).read())
    if d.get("errors"): raise SystemExit("RunPod error: " + json.dumps(d["errors"])[:600])
    return d["data"]
def me(): return gql("query { myself { clientBalance currentSpendPerHr networkVolumes { id name size dataCenterId } pods { id name desiredStatus costPerHr networkVolumeId machine { gpuDisplayName } runtime { uptimeInSeconds ports { ip isIpPublic privatePort publicPort type } } } } }")["myself"]
def volume():
    for v in me()["networkVolumes"]:
        if v["name"] == VOL: return v
    v = gql("mutation($i: CreateNetworkVolumeInput!) { createNetworkVolume(input: $i) { id name size dataCenterId } }",
            {"i": {"name": VOL, "size": 60, "dataCenterId": DC}})["createNetworkVolume"]; print("created", v); return v
def up(gpu, name="ed-train"):
    # No network volume: GPU supply moves between data centers, so each pod bootstraps itself (bootstrap.sh) on local disk.
    i = {"cloudType": "SECURE", "gpuCount": 1, "gpuTypeId": gpu, "name": name, "imageName": IMAGE, "templateId": "runpod-torch-v280", "containerDiskInGb": 120, "volumeInGb": 0,
         "ports": "8888/http,22/tcp", "startSsh": True, "env": [{"key": "PUBLIC_KEY", "value": PUB}]}
    p = gql("mutation($i: PodFindAndDeployOnDemandInput) { podFindAndDeployOnDemand(input: $i) { id name costPerHr machine { gpuDisplayName } } }", {"i": i})["podFindAndDeployOnDemand"]
    print("deployed", p)
def ssh():
    for p in me()["pods"]:
        if not p["name"].startswith("ed-"): continue
        ports = ((p.get("runtime") or {}).get("ports")) or []
        s = [f"root@{x['ip']} -p {x['publicPort']}" for x in ports if x["privatePort"] == 22 and x["isIpPublic"]]
        print(p["id"], p["name"], p["machine"]["gpuDisplayName"] if p.get("machine") else "", p["desiredStatus"], s or "starting")
def delvol():
    for v in me()["networkVolumes"]:
        if v["name"] == VOL: gql("mutation($i: DeleteNetworkVolumeInput!) { deleteNetworkVolume(input: $i) }", {"i": {"id": v["id"]}}); print("deleted", v)
def down(pid=None):
    for p in me()["pods"]:
        if p["name"].startswith("ed-") and (pid is None or p["id"] == pid):
            gql("mutation($i: PodTerminateInput!) { podTerminate(input: $i) }", {"i": {"podId": p["id"]}}); print("terminated", p["id"], p["name"])
def status():
    m = me(); print(f"balance ${m['clientBalance']:.2f} spend/hr ${m['currentSpendPerHr']:.3f}")
    print("volumes", m["networkVolumes"]); ssh()
if __name__ == "__main__":
    a = sys.argv[1:]; {"volume": lambda: print(volume()), "up": lambda: up(*a[1:]), "ssh": ssh, "down": lambda: down(*a[1:]), "status": status, "delvol": delvol}[a[0]]()
