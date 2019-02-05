import os
import gzip
import shutil
import StringIO
import time

import xbmc, xbmcaddon
from matthuisman.constants import ADDON_ID, ADDON_PROFILE
from matthuisman.session import Session
from matthuisman import settings, userdata

from .constants import FORCE_RUN_FLAG

def run():
    output_dir = settings.get('output_dir', ADDON_PROFILE)

    s = Session()

    response = s.get('http://i.mjh.nz/au/Sydney/kodi-tv.m3u8', stream=True)
    response.raise_for_status()
    with open(os.path.join(output_dir, 'playlist.m3u8'), 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)

    url = 'http://i.mjh.nz/nz/epg.xml.gz'

    r = s.get(url, stream=True)
    in_file = StringIO.StringIO(r.content)

    if url.lower().endswith('.gz'):
        in_file = gzip.GzipFile(fileobj=in_file)

    with open(os.path.join(output_dir, 'epg.xml'), 'wb') as f:
        shutil.copyfileobj(in_file, f)

    if settings.getBool('restart_pvr', False):
        xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":true}}')
        addon = xbmcaddon.Addon('pvr.iptvsimple')
        addon.setSetting('_restart', '')

def start():
    xbmc.executebuiltin('Skin.SetString({},)'.format(ADDON_ID))

    monitor = xbmc.Monitor()
    while not monitor.waitForAbort(1):
        if xbmc.getInfoLabel('Skin.String({})'.format(ADDON_ID)) == FORCE_RUN_FLAG or time.time() - userdata.get('last_run', 0) > settings.getInt('reload_time_mins') * 60:
            run()
            userdata.set('last_run', int(time.time()))
            xbmc.executebuiltin('Skin.SetString({},)'.format(ADDON_ID))