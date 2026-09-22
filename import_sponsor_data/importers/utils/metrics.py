import re


class Metrics:
    metrics: dict

    def __init__(self):
        self.metrics = dict()

    def simplify_path(self, path: str):
        parts = path.rsplit("--", 1)
        path = parts[0].split("?", 1)[0]
        if len(parts) > 1:
            path = f"{path} - {parts[1]}"
        path = re.sub(r"_[0-9]{6}\/", "_NNNNNN/", path)
        return path

    def icrement(self, key: str):
        key = self.simplify_path(key)
        self.metrics[key] = self.metrics.get(key, 0) + 1

    def icrement(self, key: str, increment: int = 1):
        key = self.simplify_path(key)
        self.metrics[key] = self.metrics.get(key, 0) + increment

    def print(self, sort_by_number=False):
        print("----------------------------------------")
        print("Metrics")
        print("----------------------------------------")
        for kv in self.metrics.items():
            print("{}:{}".format(kv[0], kv[1]))
        print("----------------------------------------")

    def print_sorted_by_value(self):
        data = sorted(self.metrics.items(), key=lambda x: x[1], reverse=True)
        print("----------------------------------------")
        print("Metrics, sorted by number of calls")
        print("----------------------------------------")
        for kv in data:
            print("{}:{}".format(kv[0], kv[1]))
        print("----------------------------------------")

    def print_sorted_by_key(self):
        data = sorted(self.metrics.items(), key=lambda x: x[0])
        print("----------------------------------------")
        print("Metrics, sorted alphabetically by endpoint")
        print("----------------------------------------")
        for kv in data:
            print("{}:{}".format(kv[0], kv[1]))
        print("----------------------------------------")
