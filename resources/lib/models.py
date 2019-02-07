import xbmcgui

from matthuisman import peewee, database, gui

from .language import _

class IPTV(database.Model):
    ITEM_PLAYLIST = 0
    ITEM_EPG = 1

    TYPE_REMOTE = 0
    TYPE_LOCAL  = 1
    TYPE_ADDON  = 2

    FILE_TEXT = 0
    FILE_GZIP = 1

    item_type     = peewee.IntegerField()
    path_type     = peewee.IntegerField()
    path          = peewee.TextField()
    file_type     = peewee.IntegerField()

    def label(self):
        if self.item_type == self.ITEM_PLAYLIST:
            return _(_.ITEM_LABEL, type=_.PLAYLIST, path=self.path)
        else:
            return _(_.ITEM_LABEL, type=_.EPG, path=self.path)

    def wizard(self):
        types = [self.ITEM_PLAYLIST, self.ITEM_EPG]
        options = [_.PLAYLIST, _.EPG]

        index = gui.select(_.CHOOSE, options)
        if index < 0:
            return False

        self.item_type = types[index]

        types = [self.TYPE_REMOTE, self.TYPE_LOCAL]
        options = [_.REMOTE_PATH, _.LOCAL_PATH]

        index = gui.select(_.CHOOSE, options)
        if index < 0:
            return False

        self.path_type = types[index]

        if self.path_type == self.TYPE_REMOTE:
            self.path = gui.input(_.URL, default=self.path)
        elif self.path_type == self.TYPE_LOCAL:
            self.path = xbmcgui.Dialog().browseSingle(1, _.BROWSE_FILE, self.path or '', '')

        if not self.path:
            return False

        types = [self.FILE_TEXT, self.FILE_GZIP]
        options = [_.STANDARD_FILE, _.GZIPPED_FILE]

        index = gui.select(_.CHOOSE, options)
        if index < 0:
            return False

        self.file_type = types[index]

        return True

database.tables.append(IPTV)