import xbmcgui

from matthuisman import peewee, database, gui

from .language import _

# TYPES = {
#     'Remote Path': TYPE_REMOTE,
#     'Local Path': TYPE_LOCAL,
#     'Addon': TYPE_ADDON,
# }

class IPTV(database.Model):
    ITEM_PLAYLIST = 0
    ITEM_EPG = 1

    TYPE_REMOTE = 0
    TYPE_LOCAL  = 1
    TYPE_ADDON  = 2

    FILE_TEXT = 0
    FILE_GZIP = 1

    item_type     = peewee.IntegerField()

    enabled       = peewee.BooleanField(default=True)
    
    path_type     = peewee.IntegerField(default=TYPE_REMOTE)
    path          = peewee.TextField(null=True)
    file_type     = peewee.IntegerField(default=FILE_TEXT)

database.tables.append(IPTV)