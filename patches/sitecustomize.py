import fastapi as _f

_orig = _f.FastAPI.__init__


def _new(self, *a, **kw):
    _orig(self, *a, **kw)
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator(excluded_handlers=["/metrics"]).instrument(self).expose(
            self, include_in_schema=False
        )
    except Exception:
        pass


_f.FastAPI.__init__ = _new
