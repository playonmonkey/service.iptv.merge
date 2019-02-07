from matthuisman.language import BaseLanguage

class Language(BaseLanguage):
    SETTING_FETCH_EVERY_X  = 30000
    SETTING_AUTO_RELOAD    = 30001
    SETTING_FILES_DIR      = 30002
    SETTING_IPTV_SIMPLE    = 30003

    ADD_PLAYLIST_EPG       = 30004
    GENERATE_NOW           = 30005

    DELETE_ITEM            = 30006
    CONFIRM_DELETE_ITEM    = 30007
    GENERATE_OK            = 30008

    ITEM_LABEL             = 30009
    PLAYLIST               = 30010
    EPG                    = 30011
    CHOOSE                 = 30012
    REMOTE_PATH            = 30013
    LOCAL_PATH             = 30014
    URL                    = 30015
    BROWSE_FILE            = 30016
    STANDARD_FILE          = 30017
    GZIPPED_FILE           = 30018

_ = Language()