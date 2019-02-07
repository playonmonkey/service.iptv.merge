import os
import gzip
import shutil
import StringIO
import time

import xml.etree.ElementTree as ET

import xbmc, xbmcaddon
from matthuisman.constants import ADDON_ID
from matthuisman.session import Session
from matthuisman import settings, userdata, database

from .constants import FORCE_RUN_FLAG, PLAYLIST_FILE_NAME, EPG_FILE_NAME, IPTV_SIMPLE_ID
from .models import IPTV

def process(item):
    if item.path_type == IPTV.TYPE_REMOTE:
        r = Session().get(item.path, stream=True)
        r.raise_for_status()
        in_file = StringIO.StringIO(r.content)
    elif item.path_type == IPTV.TYPE_LOCAL:
        in_file = open(xbmc.translatePath(item.path))
    elif item.path_type == IPTV.TYPE_ADDON:
        raise Exception('Not Implemented')

    if item.file_type == IPTV.FILE_GZIP:
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
    print("RUN MERGE!")
    output_dir = xbmc.translatePath(settings.get('output_dir'))
    if not output_dir:
        return

    database.connect()
    playlists = list(IPTV.select().where(IPTV.item_type == IPTV.ITEM_PLAYLIST))
    epgs      = list(IPTV.select().where(IPTV.item_type == IPTV.ITEM_EPG))
    database.close()

    playlist = merge_playlists(playlists)
    epg      = merge_epgs(epgs)

    with open(os.path.join(output_dir, PLAYLIST_FILE_NAME), 'wb') as f:
        f.write(playlist)

    with open(os.path.join(output_dir, EPG_FILE_NAME), 'wb') as f:
        f.write(epg)

def check_reload():
    return check_force_flag() or not check_files() or time.time() - userdata.get('last_run', 0) > settings.getInt('reload_time_mins') * 60

def check_files():
    output_dir = xbmc.translatePath(settings.get('output_dir'))
    if not output_dir:
        print("NO OUTPUT")
        return True

    return os.path.exists(os.path.join(output_dir, PLAYLIST_FILE_NAME)) and os.path.exists(os.path.join(output_dir, EPG_FILE_NAME))

def check_force_flag():
    return xbmc.getInfoLabel('Skin.String({})'.format(ADDON_ID)) == FORCE_RUN_FLAG

def reset_force_flag():
    xbmc.executebuiltin('Skin.SetString({},)'.format(ADDON_ID))

def start():
    monitor = xbmc.Monitor()
    restart_required = False
    reset_force_flag()

    while not monitor.waitForAbort(5):
        if check_reload():
            try:
                run_merge()

                if settings.getBool('restart_pvr', False):
                    restart_required = True
            except:
                pass

            userdata.set('last_run', int(time.time()))
            reset_force_flag()

        if restart_required and not xbmc.getCondVisibility('Pvr.IsPlayingTv') and not xbmc.getCondVisibility('Pvr.IsPlayingRadio'):
            restart_required = False
            xbmc.executebuiltin('InstallAddon(pvr.demo)', True)
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.demo","enabled":true}}')
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.demo","enabled":false}}')