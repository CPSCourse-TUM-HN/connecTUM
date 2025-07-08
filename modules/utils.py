class dotdict(dict):
    """Recursively accessible dict using dot notation."""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.update(*args, **kwargs)

    def __getattr__(self, key): return self[key]
    def __setattr__(self, key, value): self[key] = value
    def __delattr__(self, key): del self[key]

    def __setitem__(self, key, value):
        super().__setitem__(key, dotdict(value) if isinstance(value, dict) else value)

    def update(self, *args, **kwargs):
        super().update({k: dotdict(v) if isinstance(v, dict) else v 
                        for k, v in dict(*args, **kwargs).items()})
        