class CaselessDict(dict):
    def __init__(self, initval: dict | None = None):
        if initval is None:
            initval = {}

        if isinstance(initval, dict):
            for key, value in initval.items():
                self.__setitem__(key, value)
        elif initval is not None:
            raise ValueError(
                f"Initial value must be a dict, type {type(initval)} is not allowed."
            )

    def __contains__(self, key):
        if key is None:
            return False
        if not isinstance(key, str):
            raise ValueError(f"Key must be a string, type {type(key)} is not allowed.")
        return dict.__contains__(self, key.lower())

    def __getitem__(self, key):
        if key is None:
            return None
        if not isinstance(key, str):
            raise ValueError(f"Key must be a string, type {type(key)} is not allowed.")
        return dict.__getitem__(self, key.lower())

    def __setitem__(self, key, value):
        if key is None:
            return None
        if not isinstance(key, str):
            raise ValueError(f"Key must be a string, type {type(key)} is not allowed.")
        return dict.__setitem__(self, key.lower(), value)

    def get(self, key, default=None):
        try:
            return dict.__getitem__(self, key.lower())
        except KeyError:
            return default

    def update(self, data):
        caseless_data = CaselessDict(data)
        dict.update(self, caseless_data)
