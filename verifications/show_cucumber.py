import json

with open("cucumber.json") as f:
    data = json.load(f)

reqs = {}

for feature in data:
    tags = feature["tags"]
    feature_name = feature["name"]
    passed = []
    failed = []
    for scenario in feature["elements"]:
        scenario_name = scenario["name"]
        for step in scenario["steps"]:
            desc = f"{feature_name}; {scenario_name}; {step['keyword']} {step['name']}"
            if step["result"]["status"] == "passed":
                passed.append(desc)
            elif step["result"]["status"] == "failed":
                failed.append(desc)

    for tag in tags:
        req_nbr = tag["name"].split(":")[1]
        if req_nbr in reqs:
            reqs[req_nbr]["failed"].extend(failed)
            reqs[req_nbr]["passed"].extend(passed)
        else:
            reqs[req_nbr] = {"failed": failed, "passed": passed}

        if len(failed) > 0:
            reqs[req_nbr]["status"] = "failed"

        elif len(passed) > 0:
            reqs[req_nbr]["status"] = "passed"

print(json.dumps(reqs, indent=2))

pass_fail = {}
for req, result in reqs.items():
    pass_fail[req] = result["status"]

print(json.dumps(pass_fail, indent=2))
