from matthuisman import plugin, settings

from .language import _
from .models import Playlist, EPG

@plugin.route('')
def home():
    folder = plugin.Folder()
    return folder