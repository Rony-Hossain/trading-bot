# Minimal pandas stub so import doesn’t fail during import smoke.
class DataFrame:
    def __init__(self, *a, **k): pass
    def to_dict(self, *a, **k): return {}
    def head(self, *a, **k): return self
    def tail(self, *a, **k): return self

def read_csv(*a, **k): return DataFrame()
__version__ = "0.0-ci-stub"
