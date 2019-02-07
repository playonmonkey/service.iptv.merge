import xbmc, xbmcaddon

from matthuisman import plugin, settings, database, gui
from matthuisman.constants import ADDON_ID

from .language import _
from .models import Source
from .constants import FORCE_RUN_FLAG

@plugin.route('')
def home():
    folder = plugin.Folder()

    database.connect()
    sources = list(Source.select())
    database.close()

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
        label = _(_.ADD_SOURCE, _bold=len(sources) == 0), 
        path  = plugin.url_for(edit_source),
    )

    folder.add_item(
        label = _.MERGE_NOW, 
        path  = plugin.url_for(merge),
    )

    folder.add_item(label=_.SETTINGS, path=plugin.url_for(plugin.ROUTE_SETTINGS))

    return folder

@plugin.route()
def delete_source(id):
    source = Source.get_by_id(id)
    if gui.yes_no(_.CONFIRM_DELETE_SOURCE) and source.delete_instance():
        gui.refresh()

@plugin.route()
def edit_source(id=None):
    if id:
        source = Source.get_by_id(id)
    else:
        source = Source()

    if source.wizard():
        source.save()
        gui.refresh()

@plugin.route()
def merge():
    xbmc.executebuiltin('Skin.SetString({},{})'.format(ADDON_ID, FORCE_RUN_FLAG))
    gui.notification(_.MERGE_STARTED)