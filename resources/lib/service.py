import os
import gzip
import shutil
import StringIO
import time
import imp
import sys

import xml.etree.ElementTree as ET

import xbmc, xbmcaddon
from matthuisman.log import log
from matthuisman.constants import ADDON_ID
from matthuisman.session import Session
from matthuisman.exceptions import Error
from matthuisman import settings, userdata, database, gui

from .constants import FORCE_RUN_FLAG, PLAYLIST_FILE_NAME, EPG_FILE_NAME, PVR_ADDON_IDS, METHOD_PLAYLIST, METHOD_EPG, MERGE_MODULE
from .models import Source
from .language import _

def process(item, item_type):
    if item.path_type == Source.TYPE_ADDON:
        _opath = sys.path[:]
        _ocwd = os.getcwd()

        try:
            addons_path = xbmc.translatePath('special://home/addons').decode("utf-8")
            addon_path = os.path.join(addons_path, item.path)

            os.chdir(addon_path)
            sys.path.insert(0, addon_path)
            os.environ['ADDON_ID'] = item.path

            f, filename, description = imp.find_module(item.path, [addons_path])
            package = imp.load_module(item.path, f, filename, description)

            f, filename, description = imp.find_module(MERGE_MODULE, package.__path__)
            try:
                module = imp.load_module('{}.{}'.format(item.path, MERGE_MODULE), f, filename, description)

                if item_type == Source.PLAYLIST:
                    method = getattr(module, METHOD_PLAYLIST)
                elif item_type == Source.EPG:
                    method = getattr(module, METHOD_EPG)

                return method()
            finally:
                f.close()
        finally:
            sys.path = _opath
            os.chdir(_ocwd)
            del os.environ['ADDON_ID']

    elif item.path_type == Source.TYPE_REMOTE:
        r = Session().get(item.path, stream=True)
        r.raise_for_status()
        in_file = StringIO.StringIO(r.content)
        
    elif item.path_type == Source.TYPE_LOCAL:
        in_file = open(xbmc.translatePath(item.path))

    if item.file_type == Source.FILE_GZIP:
        in_file = gzip.GzipFile(fileobj=in_file)

    return in_file.read()

def merge_playlists(playlists):
    merged = ''

    for playlist in playlists:
        merged += '\n\n' + process(playlist, Source.PLAYLIST)

    return merged

def merge_epgs(epgs):
    channels = []
    programs = []

    for epg in epgs:
        xml = process(epg, Source.EPG)
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
        xbmc.executebuiltin('Skin.SetString({},)'.format(ADDON_ID))

        if forced or time.time() - userdata.get('last_run', 0) > settings.getInt('reload_time_mins') * 60:
            try:
                run_merge()
            except Exception as e:
                result = False
                log.exception(e)
            else:
                result = True

            userdata.set('last_run', int(time.time()))

            if result:
                restart_required = settings.getBool('restart_pvr', False)

                if forced:
                    gui.notification(_.MERGE_COMPLETE)

            elif forced:
                gui.exception()

        if restart_required and not xbmc.getCondVisibility('Pvr.IsPlayingTv') and not xbmc.getCondVisibility('Pvr.IsPlayingRadio'):
            restart_required = False
            
            addon_id = PVR_ADDON_IDS[settings.getInt('unused_pvr_id')]
            xbmc.executebuiltin('InstallAddon({})'.format(addon_id), True)
            xbmc.executeJSONRPC('{{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{{"addonid":"{}","enabled":true}}}}'.format(addon_id))
            xbmc.executeJSONRPC('{{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{{"addonid":"{}","enabled":false}}}}'.format(addon_id))