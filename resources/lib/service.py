import os
import gzip
import shutil
import StringIO
import time

import xml.etree.ElementTree as ET

import xbmc, xbmcaddon
from matthuisman.constants import ADDON_ID, ADDON_PROFILE
from matthuisman.session import Session
from matthuisman import settings, userdata, database

from .constants import FORCE_RUN_FLAG, PLAYLIST_FILE_NAME, EPG_FILE_NAME
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

def run():
    output_dir = settings.get('output_dir')
    output_dir = xbmc.translatePath(output_dir)
    out_playlist = ''

    database.connect()
    playlists = list(IPTV.select().where(IPTV.item_type == IPTV.ITEM_PLAYLIST, IPTV.enabled == True))
    epgs      = list(IPTV.select().where(IPTV.item_type == IPTV.ITEM_EPG, IPTV.enabled == True))
    database.close()

    for playlist in playlists:
        out_playlist += '\n' + process(playlist)

    with open(os.path.join(output_dir, PLAYLIST_FILE_NAME), 'wb') as f:
        f.write(out_playlist)

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
        
    output = b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE tv SYSTEM "xmltv.dtd">\n' +  ET.tostring(root_element, encoding="utf-8")
    with open(os.path.join(output_dir, EPG_FILE_NAME), 'wb') as f:
        f.write(output)

    userdata.set('last_run', int(time.time()))
    xbmc.executebuiltin('Skin.SetString({},)'.format(ADDON_ID))

def start():
    restart_required = False

    xbmc.executebuiltin('Skin.SetString({},)'.format(ADDON_ID))

    monitor = xbmc.Monitor()
    while not monitor.waitForAbort(5):
        if xbmc.getInfoLabel('Skin.String({})'.format(ADDON_ID)) == FORCE_RUN_FLAG or time.time() - userdata.get('last_run', 0) > settings.getInt('reload_time_mins') * 60:
            if run() and settings.getBool('restart_pvr', False):
                restart_required = True
        
        if restart_required and not xbmc.getCondVisibility('Pvr.IsPlayingTv') and not xbmc.getCondVisibility('Pvr.IsPlayingRadio'):
            restart_required = False
            addon = xbmcaddon.Addon('pvr.iptvsimple')
            addon.setSetting('_restart', '')