import os
import json

import xbmc, xbmcgui, xbmcaddon

from matthuisman import peewee, database, gui
from matthuisman.exceptions import Error

from .constants import MERGE_FILENAME
from .language import _

class Source(database.Model):
    PLAYLIST = 0
    EPG = 1

    TYPE_REMOTE = 0
    TYPE_LOCAL  = 1
    TYPE_ADDON  = 2

    FILE_STANDARD = 0
    FILE_GZIP     = 1

    item_type     = peewee.IntegerField()
    path_type     = peewee.IntegerField()
    path          = peewee.TextField()
    file_type     = peewee.IntegerField(null=True)

    def label(self):
        if self.path_type == self.TYPE_ADDON:
            try:
                return '{} ({})'.format(xbmcaddon.Addon(self.path).getAddonInfo('name'), self.path)
            except:
                return self.path
        else:
            return self.path

    def wizard(self):
        types   = [self.TYPE_REMOTE, self.TYPE_LOCAL, self.TYPE_ADDON]
        options = [_.REMOTE_PATH, _.LOCAL_PATH, _.ADDON_SOURCE]
        default = self.path_type or self.TYPE_REMOTE

        index   = gui.select(_.CHOOSE, options, preselect=types.index(default))
        if index < 0:
            return False

        self.path_type = types[index]

        if self.path_type == self.TYPE_ADDON:
            addons  = self._get_merge_addons()
            if not addons:
                raise Error(_.NO_ADDONS)

            ids     = [x['id'] for x in addons]
            options = [x['name'] for x in addons]

            try:
                default = ids.index(self.path)
            except ValueError:
                default = 0

            index = gui.select(_.CHOOSE, options, preselect=default)
            if index < 0:
                return False

            self.path = ids[index]
            return True

        elif self.path_type == self.TYPE_REMOTE:
            self.path = gui.input(_.URL, default=self.path)
        elif self.path_type == self.TYPE_LOCAL:
            self.path = xbmcgui.Dialog().browseSingle(1, _.BROWSE_FILE, self.path or '', '')

        if not self.path:
            return False

        types   = [self.FILE_STANDARD, self.FILE_GZIP]
        options = [_.STANDARD_FILE, _.GZIPPED_FILE]
        default = self.file_type or (self.FILE_GZIP if self.path.endswith('.gz') else self.FILE_STANDARD)

        index   = gui.select(_.CHOOSE, options, preselect=types.index(default))
        if index < 0:
            return False

        self.file_type = types[index]

        return True

    def _get_merge_addons(self):
        addons = []

        addons_path = xbmc.translatePath('special://home/addons').decode("utf-8")
        for addon_id in os.listdir(addons_path):
            addon_path = os.path.join(addons_path, addon_id)
            merge_path = os.path.join(addon_path, MERGE_FILENAME)

            if not os.path.exists(merge_path):
                continue

            try:
                name = xbmcaddon.Addon(addon_id).getAddonInfo('name')
            except:
                name = addon_id

            addons.append({'name': name, 'id': addon_id})

        return addons

database.tables.append(Source)