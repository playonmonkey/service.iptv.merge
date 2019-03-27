import xbmc, xbmcaddon

from matthuisman import plugin, settings, database, gui
from matthuisman.constants import ADDON_ID

from .language import _
from .models import Source
from .constants import FORCE_RUN_FLAG

@plugin.route('')
def home():
    folder = plugin.Folder()

    folder.add_item(
        label = _(_.PLAYLISTS, _bold=True), 
        path  = plugin.url_for(playlists),
    )

    folder.add_item(
        label = _(_.EPGS, _bold=True), 
        path  = plugin.url_for(epgs),
    )

    folder.add_item(
        label = _.MERGE_NOW, 
        path  = plugin.url_for(merge),
    )

    folder.add_item(label=_.SETTINGS, path=plugin.url_for(plugin.ROUTE_SETTINGS))

    return folder

@plugin.route()
def playlists():
    folder = plugin.Folder(title=_.PLAYLISTS)
    sources = list(Source.select().where(Source.item_type == Source.PLAYLIST))

    for source in sources:
        item = plugin.Item(
            label = source.label(),
            path = plugin.url_for(edit_source, id=source.id),
            is_folder = False,
            playable = False,
        )

        item.context.append((_.DELETE_SOURCE, 'XBMC.RunPlugin({})'.format(plugin.url_for(delete_source, id=source.id))))

        folder.add_items([item])

    folder.add_item(
        label = _(_.ADD_PLAYLIST, _bold=len(sources) == 0), 
        path  = plugin.url_for(edit_source, type=Source.PLAYLIST),
    )

    return folder

@plugin.route()
def epgs():
    folder = plugin.Folder(title=_.EPGS)
    sources = list(Source.select().where(Source.item_type == Source.EPG))

    for source in sources:
        item = plugin.Item(
            label = source.label(),
            path = plugin.url_for(edit_source, id=source.id),
            is_folder = False,
            playable = False,
        )

        item.context.append((_.DELETE_SOURCE, 'XBMC.RunPlugin({})'.format(plugin.url_for(delete_source, id=source.id))))

        folder.add_items([item])

    folder.add_item(
        label = _(_.ADD_EPG, _bold=len(sources) == 0), 
        path  = plugin.url_for(edit_source, type=Source.EPG),
    )

    return folder

@plugin.route()
def delete_source(id):
    source = Source.get_by_id(id)
    if gui.yes_no(_.CONFIRM_DELETE_SOURCE) and source.delete_instance():
        gui.refresh()

@plugin.route()
def edit_source(id=None, type=None):
    if id:
        source = Source.get_by_id(id)
    else:
        source = Source(item_type=type)

    if source.wizard():
        source.save()
        gui.refresh()

@plugin.route()
def merge():
    if not settings.get('output_dir'):
        raise plugin.PluginError(_.NO_OUTPUT_DIR)

    xbmc.executebuiltin('Skin.SetString({},{})'.format(ADDON_ID, FORCE_RUN_FLAG))
    gui.notification(_.MERGE_STARTED)