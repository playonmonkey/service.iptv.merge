import sys

from functools import wraps

import xbmc, xbmcplugin

from . import router, gui, settings, database, cache, userdata, inputstream, signals
from .constants import ROUTE_SETTINGS, ROUTE_RESET, ROUTE_SERVICE, ROUTE_CLEAR_CACHE, ROUTE_IA_SETTINGS, ROUTE_IA_INSTALL, ADDON_ICON, ADDON_FANART, ADDON_ID
from .log import log
from .language import _
from .exceptions import PluginError

## SHORTCUTS
url_for         = router.url_for
dispatch        = router.dispatch
############

def exception(msg=''):
    raise PluginError(msg)

logged_in   = False

# @plugin.login_required()
def login_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not logged_in:
                raise PluginError(_.PLUGIN_LOGIN_REQUIRED)

            return f(*args, **kwargs)
        return decorated_function
    return lambda f: decorator(f)

# @plugin.route()
def route(url=None):
    def decorator(f, url):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            item = f(*args, **kwargs)

            if isinstance(item, Folder):
                item.display()
            elif isinstance(item, Item):
                item.play()
            else:
                resolve()

        router.add(url, decorated_function)
        return decorated_function
    return lambda f: decorator(f, url)

def resolve():
    if _handle() > 0:
        xbmcplugin.endOfDirectory(_handle(), succeeded=False, updateListing=False, cacheToDisc=False)
    
@signals.on(signals.BEFORE_DISPATCH)
def _open():
    database.connect()
    cache.remove_expired()

@signals.on(signals.ON_ERROR)
def _error(e):
    try:
        error = str(e)
    except:
        error = e.message.encode('utf-8')

    if not hasattr(e, 'heading'):
        e.heading = _.PLUGIN_ERROR

    log.error(error)
    _close()

    gui.ok(error, heading=e.heading)
    resolve()

@signals.on(signals.ON_EXCEPTION)
def _exception(e):
    log.exception(e)
    _close()
    gui.exception()
    resolve()

@signals.on(signals.AFTER_DISPATCH)
def _close():
    database.close()

@route('')
def _home():
    raise PluginError(_.PLUGIN_NO_DEFAULT_ROUTE)

@route(ROUTE_IA_SETTINGS)
def _ia_settings():
    _close()
    inputstream.open_settings()

@route(ROUTE_IA_INSTALL)
def _ia_install():
    _close()
    inputstream.install_widevine(reinstall=True)

def reboot():
    _close()
    xbmc.executebuiltin('Reboot')

@route(ROUTE_SETTINGS)
def _settings():
    _close()
    settings.open()
    gui.refresh()

@route(ROUTE_RESET)
def _reset():
    if not gui.yes_no(_.PLUGIN_RESET_YES_NO):
        return

    userdata.clear()
    database.delete()
    gui.notification(_.PLUGIN_RESET_OK)
    signals.emit(signals.AFTER_RESET)

@route(ROUTE_CLEAR_CACHE)
def _clear_cache(key):
    delete_count = cache.delete(key)
    msg = _(_.PLUGIN_CACHE_REMOVED, delete_count=delete_count)
    gui.notification(msg)

@route(ROUTE_SERVICE)
def _service():
    try:
        signals.emit(signals.ON_SERVICE)
    except Exception as e:
        #catch all errors so dispatch doesn't show error
        log.exception(e)

def _handle():
    try:
        return int(sys.argv[1])
    except:
        return -1

#Plugin.Item()
class Item(gui.Item):
    def __init__(self, cache_key=None, *args, **kwargs):
        art = kwargs.pop('art', None)
        if art != False:
            new_art = {'fanart': ADDON_FANART, 'thumb': ADDON_ICON}
            if art:
                for key in art:
                    if art[key]:
                        new_art[key] = art[key]

            art = new_art

        super(Item, self).__init__(self, *args, art=art, **kwargs)
        self.cache_key = cache_key

    def get_li(self):
        if cache.enabled() and self.cache_key:
            url = url_for(ROUTE_CLEAR_CACHE, key=self.cache_key)
            self.context.append((_.PLUGIN_CONTEXT_CLEAR_CACHE, 'XBMC.RunPlugin({})'.format(url)))

        return super(Item, self).get_li()

    def play(self):
        li = self.get_li()
        handle = _handle()

        if handle > 0:
            xbmcplugin.setResolvedUrl(handle, True, li)
        else:
            xbmc.Player().play(li.getPath(), li)

#Plugin.Folder()
class Folder(object):
    def __init__(self, items=None, title=None, content='videos', updateListing=False, cacheToDisc=True):
        self.items = items or []
        self.title = title
        self.content = content
        self.updateListing = updateListing
        self.cacheToDisc = cacheToDisc

    def display(self):
        for item in self.items:
            if not item:
                continue

            li = item.get_li()
            xbmcplugin.addDirectoryItem(_handle(), li.getPath(), li, item.is_folder)

        if self.content: xbmcplugin.setContent(_handle(), self.content)
        if self.title: xbmcplugin.setPluginCategory(_handle(), self.title)

        xbmcplugin.endOfDirectory(_handle(), succeeded=True, updateListing=self.updateListing, cacheToDisc=self.cacheToDisc)

    def add_item(self, *args, **kwargs):
        item = Item(*args, **kwargs)
        self.items.append(item)
        return item

    def add_items(self, items):
        self.items.extend(items)