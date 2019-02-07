import os
import gzip
import shutil
import StringIO
import time

import xml.etree.ElementTree as ET

import xbmc, xbmcaddon
from matthuisman.log import log
from matthuisman.constants import ADDON_ID
from matthuisman.session import Session
from matthuisman import settings, userdata, database, gui

from .constants import FORCE_RUN_FLAG, PLAYLIST_FILE_NAME, EPG_FILE_NAME
from .models import Source

def process(item):
    if item.path_type == Source.TYPE_REMOTE:
        r = Session().get(item.path, stream=True)
        r.raise_for_status()
        in_file = StringIO.StringIO(r.content)
    elif item.path_type == Source.TYPE_LOCAL:
        in_file = open(xbmc.translatePath(item.path))
    elif item.path_type == Source.TYPE_ADDON:
        raise Exception('Not Implemented')

    if item.file_type == Source.FILE_GZIP:
        in_file = gzip.GzipFile(fileobj=in_file)

    return in_file.read()

def merge_playlists(playlists):
    merged = ''

    for playlist in playlists:
        merged += '\n' + process(playlist)

    return merged

def merge_epgs(epgs):
    channels = []
    programs = []

    for epg in epgs:
        xml = process(epg)
        tree = ET.fromstring(xml)
        channels.extend(tree.findall('channel'))
        programs.extend(tree.findall('programme'))

    root_element = ET.Element("tv")
    root_element.set("generator-info-name", ADDON_ID)

    root_element.extend(channels)
    root_element.extend(programs)
        
    merged = b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE tv SYSTEM "xmltv.dtd">\n' + ET.tostring(root_element, encoding="utf-8")
    return merged

def run_merge():
    output_dir = xbmc.translatePath(settings.get('output_dir'))
    if not output_dir:
        return

    database.connect()
    playlists = list(Source.select().where(Source.item_type == Source.PLAYLIST))
    epgs      = list(Source.select().where(Source.item_type == Source.EPG))
    database.close()

    playlist = merge_playlists(playlists)
    epg      = merge_epgs(epgs)

    with open(os.path.join(output_dir, PLAYLIST_FILE_NAME), 'wb') as f:
        f.write(playlist)

    with open(os.path.join(output_dir, EPG_FILE_NAME), 'wb') as f:
        f.write(epg)

def start():
    monitor = xbmc.Monitor()
    restart_required = False

    while not monitor.waitForAbort(5):
        forced = xbmc.getInfoLabel('Skin.String({})'.format(ADDON_ID)) == FORCE_RUN_FLAG

        if forced or time.time() - userdata.get('last_run', 0) > settings.getInt('reload_time_mins') * 60:
            try:
                run_merge()

                if settings.getBool('restart_pvr', False):
                    restart_required = True
            except Exception as e:
                log.exception(e)
                if forced:
                    gui.exception()

            userdata.set('last_run', int(time.time()))
            xbmc.executebuiltin('Skin.SetString({},)'.format(ADDON_ID))

        if restart_required and not xbmc.getCondVisibility('Pvr.IsPlayingTv') and not xbmc.getCondVisibility('Pvr.IsPlayingRadio'):
            restart_required = False
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.demo","enabled":true}}')
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.demo","enabled":false}}')