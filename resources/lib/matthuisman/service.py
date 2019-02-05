import xbmc

from .router import url_for
from .constants import ROUTE_SERVICE, ROUTE_SERVICE_INTERVAL

def run(interval=ROUTE_SERVICE_INTERVAL):
    url = url_for(ROUTE_SERVICE)
    cmd = 'XBMC.RunPlugin({0})'.format(url)

    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        xbmc.executebuiltin(cmd)
        if monitor.waitForAbort(interval):
            break