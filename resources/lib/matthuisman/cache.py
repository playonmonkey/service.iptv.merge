from time import time
from functools import wraps

from . import peewee, database, settings
from .constants import CACHE_TABLENAME, CACHE_EXPIRY, CACHE_CHECKSUM, CACHE_CLEAN_INTERVAL, CACHE_CLEAN_KEY
from .util import hash_6
from .log import log

funcs   = []

class Cache(database.Model):
    checksum = CACHE_CHECKSUM

    key     = database.HashField(unique=True)
    value   = database.PickledField()
    expires = peewee.IntegerField()

    class Meta:
        table_name = CACHE_TABLENAME

def enabled():
    return settings.getBool('use_cache', True)

def key_for(f, *args, **kwargs):
    func_name = f.__name__ if callable(f) else f
    if not enabled() or func_name not in funcs:
        return None

    return _build_key(func_name, *args, **kwargs)

def _build_key(func_name, *args, **kwargs):
    key = func_name

    def to_str(item):
        try:
            return item.encode('utf-8')
        except:
            return str(item)
    
    for k in sorted(args):
        key += to_str(k)

    for k in sorted(kwargs):
        key += to_str(k) + to_str(kwargs[k])

    return hash_6(key)

def cached(*args, **kwargs):
    def decorator(f, expires=CACHE_EXPIRY, key=None):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            _key = key or _build_key(f.__name__, *args, **kwargs)
            if callable(_key):
                _key = _key(*args, **kwargs)

            if not kwargs.pop('_skip_cache', False):
                value = get(_key)
                if value != None:
                    log('Cache Hit: {}'.format(_key))
                    return value

            value = f(*args, **kwargs)
            if value != None:
                set(_key, value, expires)

            return value

        funcs.append(f.__name__)
        return decorated_function

    return lambda f: decorator(f, *args, **kwargs)

def get(key, default=None):
    if not enabled():
        return default

    try:
        return Cache.get(Cache.key == key, Cache.expires > time()).value
    except Cache.DoesNotExist:
        return default

def set(key, value, expires=CACHE_EXPIRY):
    expires = int(time() + expires)
    Cache.set(key=key, value=value, expires=expires)

def delete(key):
    return Cache.delete_where(Cache.key == key)

def empty():
    deleted = Cache.truncate()
    log('Cache: Deleted {} Rows'.format(deleted))

def remove_expired():
    deleted = Cache.delete_where(Cache.expires < int(time()))
    log('Cache: Deleted {} Expired Rows'.format(deleted))

database.tables.append(Cache)