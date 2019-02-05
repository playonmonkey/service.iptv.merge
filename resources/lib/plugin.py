from matthuisman import plugin, settings

from .language import _

@plugin.route('')
def home():
    folder = plugin.Folder()
    return folder