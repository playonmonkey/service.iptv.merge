from matthuisman.language import BaseLanguage

class Language(BaseLanguage):
    SETTING_FETCH_EVERY_X  = 30000
    SETTING_AUTO_RELOAD    = 30001
    SETTING_FILES_DIR      = 30002
    ADD_EPG                = 30003
    ADD_PLAYLIST           = 30004
    MERGE_NOW              = 30005
    DELETE_SOURCE          = 30006
    CONFIRM_DELETE_SOURCE  = 30007
    MERGE_STARTED          = 30008

    PLAYLISTS              = 30010
    EPGS                   = 30011
    CHOOSE                 = 30012
    REMOTE_PATH            = 30013
    LOCAL_PATH             = 30014
    URL                    = 30015
    BROWSE_FILE            = 30016
    STANDARD_FILE          = 30017
    GZIPPED_FILE           = 30018
    UNUSED_PVR_ADDON       = 30019

_ = Language()