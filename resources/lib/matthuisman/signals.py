from collections import defaultdict

from .log import log

_signals = defaultdict(list)

AFTER_RESET     = 'after_reset'
ON_SERVICE      = 'on_service'
BEFORE_DISPATCH = 'before_dispatch'
AFTER_DISPATCH  = 'after_dispatch'
ON_ERROR        = 'on_error'
ON_EXCEPTION    = 'on_exception'

def on(signal):
    def decorator(f):
        _signals[signal].append(f)
        return f
    return decorator

def emit(signal, *args, **kwargs):
    log.debug("SIGNAL: {}".format(signal))
    for f in _signals.get(signal, []):
        f(*args, **kwargs)