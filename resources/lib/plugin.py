import xbmc, xbmcaddon

from matthuisman import plugin, settings, database, gui
from matthuisman.constants import ADDON_ID

from .language import _
from .models import IPTV
from .constants import FORCE_RUN_FLAG, IPTV_SIMPLE_ID

@plugin.route('')
def home():
    folder = plugin.Folder()

    database.connect()
    iptv_items = list(IPTV.select())
    database.close()

    for iptv_item in iptv_items:
        item = plugin.Item(
            label = iptv_item.label(),
            path = plugin.url_for(edit_item, id=iptv_item.id),
            is_folder = False,
            playable = False,
        )

        item.context.append((_.DELETE_ITEM, 'XBMC.RunPlugin({})'.format(plugin.url_for(delete_item, id=iptv_item.id))))

        folder.add_items([item])

    folder.add_item(
        label = _(_.ADD_PLAYLIST_EPG, _bold=len(iptv_items) == 0), 
        path  = plugin.url_for(edit_item),
    )

    folder.add_item(
        label = _.GENERATE_NOW, 
        path  = plugin.url_for(generate),
    )

    folder.add_item(label=_.SETTINGS, path=plugin.url_for(plugin.ROUTE_SETTINGS))

    return folder

@plugin.route()
def delete_item(id):
    item = IPTV.get_by_id(id)
    if gui.yes_no(_.CONFIRM_DELETE_ITEM) and item.delete_instance():
        gui.refresh()

@plugin.route()
def edit_item(id=None):
    if id:
        item = IPTV.get_by_id(id)
    else:
        item = IPTV()

    if item.wizard():
        item.save()
        gui.refresh()

@plugin.route()
def generate():
    xbmc.executebuiltin('Skin.SetString({},{})'.format(ADDON_ID, FORCE_RUN_FLAG))
    gui.notification(_.GENERATE_OK)

@plugin.route()
def iptv_simple_settings():
    xbmc.executebuiltin('InstallAddon({})'.format(IPTV_SIMPLE_ID), True)
    addon = xbmcaddon.Addon(IPTV_SIMPLE_ID)
    addon.openSettings()