import json, urllib.request, os
key = [l.split("=", 1)[1].strip() for l in open(os.path.expanduser("~/ethics-distill/.env")) if l.startswith("RUNPOD_API_KEY=")][0]
q = {"query": "{ gpuTypes { id displayName memoryInGb lowestPrice(input:{gpuCount:1,secureCloud:true}) { uninterruptablePrice stockStatus } } }"}
r = urllib.request.Request("https://api.runpod.io/graphql", data=json.dumps(q).encode(), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
d = json.loads(urllib.request.urlopen(r, timeout=60).read())["data"]["gpuTypes"]
for g in d:
    if any(k in g["displayName"] for k in ["A100", "H100", "H200", "B200", "RTX 6000", "L40S"]):
        p = g["lowestPrice"] or {}
        print(f'{g["displayName"]:28s} {g["memoryInGb"]:4d}GB  on-demand ${p.get("uninterruptablePrice")}  stock {p.get("stockStatus")}')
