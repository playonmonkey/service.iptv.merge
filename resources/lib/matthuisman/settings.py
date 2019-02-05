import json

from .constants import ADDON

def open():
    ADDON.openSettings()

def getDict(key, default=None):
    try:
        return json.loads(get(key))
    except:
        return default

def setDict(key, value):
    set(key, json.dumps(value))

def getInt(key, default=None):
    return int(get(key, default))

def setInt(key, value):
    set(key, int(value))

def getBool(key, default=False):
    value = get(key).lower()
    if not value:
        return default
    else:
        return value == 'true'

def remove(key):
    set(key, '')

def setBool(key, value=True):
    set(key, 'true' if value else 'false')

def get(key, default=''):
    return ADDON.getSetting(key) or default

def set(key, value=''):
    ADDON.setSetting(key, str(value))

FRESH = getBool('_fresh', True)
if FRESH:
    setBool('_fresh', False)