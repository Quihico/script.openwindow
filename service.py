import xbmcplugin, xbmcgui, xbmc, xbmcaddon, os, sys, shutil

ADDONID                    = 'script.openwindow'
ADDON                      = xbmcaddon.Addon(ADDONID)
ADDONS                     = xbmc.translatePath(os.path.join('special://home','addons',''))
HOME                       = xbmc.translatePath('special://home/')
RestoreGUI                 = os.path.join(HOME,'userdata','addon_data','service.openelec.settings','restoregui')

if os.path.exists(RestoreGUI):
    xbmc.executebuiltin('Skin.SetString(Branding,off)')
