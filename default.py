#
#       Copyright (C) 2015
#       Json Edits and Various tweaks by OpenELEQ (OpenELEQ@gmail.com)
#       Based on original work by:
#       Lee Randall (info@totalrevolution.tv)
#
#  This software is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International Public License
#  You can find a copy of the license in the add-on folder

import urllib, urllib2, re, xbmcplugin, xbmcgui, xbmc, xbmcaddon, os, sys, time, xbmcvfs, datetime, zipfile, shutil, binascii, hashlib
import downloader
import extract
import yt
import threading

try:
    import json as simplejson 
except:
    import simplejson

ADDONID                    = 'script.openwindow'
ADDON                      = xbmcaddon.Addon(ADDONID)
ADDONS                     = xbmc.translatePath(os.path.join('special://home','addons',''))
ADDONPATH                  = xbmcaddon.Addon('script.openwindow').getAddonInfo("path")
LANGUAGEPATH               = xbmc.translatePath(os.path.join(ADDONPATH,'resources','language'))
ACTION_HOME                = 7
ACTION_PREVIOUS_MENU       = 10
ACTION_SELECT_ITEM         = 7
installfile                = '/usr/share/kodi/addons/script.openwindow/default.py'
if not os.path.exists(installfile):
    installfile                = xbmc.translatePath(os.path.join(ADDONS,ADDONID,'default.py'))
dialog                     = xbmcgui.Dialog()
dp                         = xbmcgui.DialogProgress()
skin                       = xbmc.getSkinDir()
currently_downloaded_bytes = 0.0
max_Bps                    = 0.0
restore_dir                = '/storage/.restore/'
path                       = xbmc.translatePath(os.path.join('special://home/addons','packages'))
thumbnails                 = xbmc.translatePath(os.path.join('special://home','userdata','Thumbnails'))
PACKAGES                   = xbmc.translatePath(os.path.join('special://home','addons','packages',''))
HOME                       = xbmc.translatePath('special://home/')
RestoreGUI                 = os.path.join(HOME,'userdata','addon_data','service.openelec.settings','restoregui')
RunWizard                  = os.path.join(HOME,'userdata','addon_data','service.openelec.settings','runwizard')
timepath                   = os.path.join(HOME,'userdata','addon_data','service.openelec.settings','dltime')
addondata                  = os.path.join(HOME,'userdata','addon_data','service.openelec.settings')
SYSTEM                     = xbmc.translatePath('special://xbmc/')
branding_update            = xbmc.translatePath('special://home/media/branding/branding_update.png')
ipaddress                  = xbmc.getIPAddress()
log_path                   = xbmc.translatePath('special://logpath/')
m3u_file                   = xbmc.translatePath(os.path.join(HOME, 'debug.txt'))
addonfolder                = xbmc.translatePath('special://home/addons/script.openwindow/')
xbmc_version               = xbmc.getInfoLabel("System.BuildVersion")
email = ''
download_thread = ''

if not os.path.exists(addonfolder):
    addonfolder = xbmc.translatePath('special://xbmc/addons/script.openwindow/')

def OpenELEC_Check():
    xbmc_version=xbmc.getInfoLabel("System.BuildVersion")
    version=float(xbmc_version[:4])
    if version < 14:
        log_path_new = os.path.join(log_path,'xbmc.log')
    else:
        log_path_new = os.path.join(log_path,'kodi.log')
        
    try:
        localfile = open(log_path_new, mode='r')
        content   = localfile.read()
        localfile.close()
    except:
        try:
            localfile = open(os.path.join(HOME,'temp','kodi.log'), mode='r')
            content   = localfile.read()
            localfile.close()
        except:
            try:
                localfile = open(os.path.join(HOME,'temp','xbmc.log'), mode='r')
                content   = localfile.read()
                localfile.close()
            except:
                pass                
            
    if 'OpenELEC' in content:
        return True

if OpenELEC_Check():
    rootfolder                 = '/storage'
    venzpath                   = '/storage/downloads'
    if not os.path.exists(restore_dir):
        os.makedirs(restore_dir)
else:
    rootfolder = HOME
    venzpath   = xbmc.translatePath(os.path.join('special://home','..','temp_download'))

lib            = os.path.join(venzpath,'target.zip')
if not os.path.exists(venzpath):
    os.makedirs(venzpath)


if not os.path.exists(PACKAGES):
    os.makedirs(PACKAGES)


def execute(cmd):
    log(cmd)
    xbmc.executebuiltin(cmd)


def log(text):
    try:
        output = '%s : %s' % (ADDONID, str(text))
        xbmc.log(output, xbmc.LOGDEBUG)
    except:
        pass


def write(what, filelocation):
    fopen = open(filelocation, "w")
    fopen.write(what)
    fopen.close()


def setSetting(setting, value):
    setting = '"%s"' % setting

    if isinstance(value, list):
        text = ''
        for item in value:
            text += '"%s",' % str(item)

        text  = text[:-1]
        text  = '[%s]' % text
        value = text

    elif not isinstance(value, int):
        value = '"%s"' % value

    query = '{"jsonrpc":"2.0", "method":"Settings.SetSettingValue","params":{"setting":%s,"value":%s}, "id":1}' % (setting, value)
    log(query)
    response = xbmc.executeJSONRPC(query)
    log(response)


def getSetting(setting):
    try:
        setting = '"%s"' % setting
 
        query = '{"jsonrpc":"2.0", "method":"Settings.GetSettingValue","params":{"setting":%s}, "id":1}' % (setting)
        log(query)
        response = xbmc.executeJSONRPC(query)
        log(response)

        response = simplejson.loads(response)                

        if response.has_key('result'):
            if response['result'].has_key('value'):
                return response ['result']['value'] 
    except:
        pass

    return None


def getLanguage(language):
    file = xbmc.translatePath(os.path.join(LANGUAGEPATH, language, 'langinfo.xml'))

    try:        
        f    = open(file, 'r')
        text = f.read()
        f.close()
    except:
        return None

    text = text.replace(' =',  '=')
    text = text.replace('= ',  '=')
    text = text.replace(' = ', '=')

    return text


def getTZCountriesNew():
    file = xbmc.translatePath(os.path.join(ADDONPATH, 'resources', 'languagelist.txt'))

    countries = []

    try:        
        f    = open(file, 'r')
        lines = f.readlines()
        f.close()
    except:
        return countries

    for line in lines:
        if line.startswith('#'):
            continue
        items = line.split('\t')
        if len(items) < 6:
            continue

        country      = items[0]
        language     = items[1]
        dir          = items[2]
        countrycode  = items[3]
        languagecode = items[4]
        indexcode    = items[5].replace('\n', '')
        countries.append([country, language, dir, countrycode, languagecode])

    countries = sorted(countries)
    return countries


def getSkins():
    file = xbmc.translatePath(os.path.join(ADDONPATH, 'resources', 'skinlist.txt'))

    skins = []

    try:        
        f    = open(file, 'r')
        lines = f.readlines()
        f.close()
    except:
        return skins

    for line in lines:
        if line.startswith('#'):
            continue
        items = line.split('\t')
        if len(items) < 4:
            continue

        skin      = items[0]
        provider  = items[1]
        id        = items[2]
        icon      = items[3]
        index     = items[4]
        skins.append([skin, provider, id, icon, index])
    return skins


def getTZCountries():
    file = '/usr/share/zoneinfo/iso3166.tab'

    countries = []

    try:        
        f    = open(file, 'r')
        lines = f.readlines()
        f.close()
    except:
        return countries

    for line in lines:
        if line.startswith('#'):
            continue
        items = line.split('\t')
        if len(items) < 2:
            continue

        code    = items[0]
        country = items[1].replace('\n', '')
        countries.append([country, code])

    countries = sorted(countries)
    return countries


def getTZ(theCode):
    file = '/usr/share/zoneinfo/zone.tab'

    zones = []

    try:        
        f    = open(file, 'r')
        lines = f.readlines()
        f.close()
    except:
        return zones

    for line in lines:
        if line.startswith('#'):
            continue
        items = line.split('\t')
        if len(items) < 3:
            continue

        code     = items[0]
        location = items[1]
        zone     = items[2].replace('\n', '')

        if code != theCode:
            if len(zones) > 0:
                #this logic assumes same codes are sequential in file
                break
        else:
            zones.append(zone)

    zones = sorted(zones)
    return zones


def getCharsets():
    file = xbmc.translatePath(os.path.join(ADDON.getAddonInfo('path'), 'resources', 'charset.txt'))

    default  = xbmc.getLocalizedString(13278)

    charsets = []
    try:        
        f      = open(file, 'r')
        lines = f.readlines()
        f.close()
    except:
        return charsets

    for line in lines:
        line = line.replace('"',  '')
        line = line.replace('\r', '')
        line = line.replace('\n', '')
        line = line.split(',')
        if len(line) < 2:
            continue

        charsets.append([line[1].strip(), line[0].strip()])

    charsets = sorted(charsets)
    charsets.insert(0, [default, 'DEFAULT'])
    return charsets


def doSetSubtitleCharset():
    import select
    menu = []

    setting = 'subtitles.charset'
    default = xbmc.getLocalizedString(13278)

    charsets = getCharsets()

    if len(charsets) == 0:
        return

    for idx, charset in enumerate(charsets):
        menu.append([charset[0], idx])

    current = getSetting(setting)    

    for charset in charsets:
        if current == charset[1]:
            current = charset[0]
            break

    option = select.select(xbmc.getLocalizedString(31380), menu, current)

    if option < 0:
        return

    label = charsets[option][0]

    if label == current:
        return

    charset = charsets[option][1]

    if charset == current:
        return

    setSetting(setting, charset)
    execute('Skin.SetBool(SubtitleCharsetSet)')
    xbmc.executebuiltin('Skin.SetString(%s,%s)' % (setting, label))


def doSetTZ():
    import select
    menu = []

    setting = 'locale.timezone'
    
    code      = '??'
    countries = getTZCountries()
    country   = getSetting('locale.timezonecountry')

    for item in countries:
        if country.lower() == item[0].lower():
            code = item[1]
            break

    timezones = getTZ(code)

    if len(timezones) == 0:
        return
        
    for idx, zone in enumerate(timezones):
        menu.append([zone, idx])

    current = getSetting(setting)
     
    option = select.select(xbmc.getLocalizedString(14080), menu, current)

    if option < 0:
        return

    tz = menu[option][0]

    if tz == current:
        return

    setSetting(setting, tz)
    execute('Skin.SetBool(TimezoneSet)')
    refreshSkinString(setting)


def doSetTZCountry():
    import select
    menu = []

    setting = 'locale.timezonecountry'
    
    countries = getTZCountries()
        
    for idx, country in enumerate(countries):
        menu.append([country[0], idx])

    current = getSetting(setting)
     
    option = select.select(xbmc.getLocalizedString(14080), menu, current) #14079 = 'Timezone country'

    if option < 0:
        return

    tz = menu[option][0]

    if tz == current:
        return

    setSetting(setting, tz)
    execute('Skin.SetBool(TimezoneCountrySet)')
    refreshSkinString(setting)


def doSetLanguage():
    import select
    import re

    menu = []
    setting = 'locale.language'
    countries = getTZCountriesNew()
    flagDir = xbmc.translatePath(os.path.join(ADDONPATH, 'resources', 'flags'))
    current = getSetting(setting)
    pretemp = str(current)
    tempM3u = "languages=\n"
    tempM3u += pretemp
    write(tempM3u, m3u_file)

    index = ''

    for item in countries:
        try:
            precountry  = "("+item[1]+")"
            country  = precountry.replace("_", " ")
            flagname = item[4]
            flag  = os.path.join(flagDir, '%s.png' % flagname)
            prelanguagename  = item[0]
            languagename  = prelanguagename.replace("_", " ")
            dir  = item[2]
            valid = os.path.exists(flag)
            index = item[5]
        except:
            pass

        if not valid:
            flag = getUnknownFlag(dir)
            flag = os.path.join(flagDir, '%s.png' % flag)
        menu.append([languagename+" "+country, dir, flag, index])

    option = select.select(xbmc.getLocalizedString(309), menu, current) #248 - Language
    language = option

    if language == current:
        return

    setSetting(setting, language)
    setSetting('locale.charset', 'DEFAULT')
    execute('Skin.SetBool(LanguageSet)')
    refreshSkinString(setting)
    return
    #setSetting(setting, language)
    #xbmc.executebuiltin("RunScript(script.openwindow,mode=selectregion)")
    #return

def doSetSkin():
    import select
    import re

    menu = []
    setting = 'lookandfeel.skin'
    skins   = getSkins()
    current = getSetting(setting)
    path    = os.path.join(SYSTEM, 'addons')
    secpath = os.path.join(HOME, 'addons')
    index   = ''
    icon    = ''

    for item in skins:
        try:
            skin      = item[0]
            provider  = item[1]
            id        = item[2]
            addonpath = os.path.join(path, id, 'icon.png')
            iconpath  = os.path.join(addonpath, 'icon.png')
            icon      = item[3]
            index     = item[4]
            valid     = os.path.exists(addonpath)
        except:
            pass
        if not valid:
            addonpath = os.path.join(secpath, id, 'icon.png')
            iconpath  = os.path.join(addonpath, 'icon.png')
        menu.append([skin, id, addonpath, index])
        pretemp = str(menu)
        tempM3u = "menu=\n"
        tempM3u += "menu=\n"
        tempM3u += pretemp
        write(tempM3u, m3u_file)
    current = getSetting(setting)
    option = select.select(xbmc.getLocalizedString(424)+" "+xbmc.getLocalizedString(166), menu, current) #248 - Language
    if option < 0:
        return

    skin = option

    if skin == current:
        return
    setSetting(setting, skin)
    while skin != current:
        xbmc.executebuiltin('Action(Select)')
        current = getSetting(setting)
    execute('Skin.SetBool(SkinSet)')
    xbmc.executebuiltin('ActivateWindow(home)')
    xbmc.executebuiltin('Notification(Please Wait 10 Seconds,And Wizard Will Continue,1100,special://skin/icon.png)')
    xbmc.sleep(1000)
    xbmc.executebuiltin('Notification(Please Wait 9 Seconds,And Wizard Will Continue,1100,special://skin/icon.png)')
    xbmc.sleep(1000)
    xbmc.executebuiltin('Notification(Please Wait 8 Seconds,And Wizard Will Continue,1100,special://skin/icon.png)')
    xbmc.sleep(1000)
    xbmc.executebuiltin('Notification(Please Wait 7 Seconds,And Wizard Will Continue,1100,special://skin/icon.png)')
    xbmc.sleep(1000)
    xbmc.executebuiltin('Notification(Please Wait 6 Seconds,And Wizard Will Continue,1100,special://skin/icon.png)')
    xbmc.sleep(1000)
    xbmc.executebuiltin('Notification(Please Wait 5 Seconds,And Wizard Will Continue,1100,special://skin/icon.png)')
    xbmc.sleep(1000)
    xbmc.executebuiltin('Notification(Please Wait 4 Seconds,And Wizard Will Continue,1100,special://skin/icon.png)')
    xbmc.sleep(1000)
    xbmc.executebuiltin('Notification(Please Wait 3 Seconds,And Wizard Will Continue,1100,special://skin/icon.png)')
    xbmc.sleep(1000)
    xbmc.executebuiltin('Notification(Please Wait 2 Seconds,And Wizard Will Continue,1100,special://skin/icon.png)')
    xbmc.sleep(1000)
    xbmc.executebuiltin('Notification(Please Wait 1 Second,And Wizard Will Continue,1100,special://skin/icon.png)')
    xbmc.sleep(1000)
    xbmc.executebuiltin('RunScript('+addonfolder+'skincontrol.py)')
#    return

    #setSetting(setting, language)
    #xbmc.executebuiltin("RunScript(script.openwindow,mode=selectregion)")
    #return


def getUnknownFlag(country):
    country = country.lower()

    if country == 'basque':                   return 'bq'
    if country == 'filipino':                 return 'ph'
    if country == 'haitian (haitian creole)': return 'ht'
    if country == 'georgian':                 return 'un'
    if country == 'lithuanian':               return 'lt'
    if country == 'mongolian (mongolia)':     return 'un'
    if country == 'romansh':                  return 'rm'
    if country == 'sinhala':                  return 'un'
    if country == 'spanish (venezuela)':      return 'un'
    if country == 'vietnamese (viet nam)':    return 'vi'

    return 'un'


def doSetSubtitleDownload():
    import select
    menu = []

    setting = 'subtitles.languages'

    skin = xbmc.getSkinDir().lower()
    path = xbmc.translatePath(os.path.join('special://home/addons/', skin, 'language'))

    try:
        current, dirs, files = os.walk(path).next()
    except:
        dirs = []

    if len (dirs) == 0:
        path = xbmc.translatePath(os.path.join('special://xbmc/addons/', skin, 'language'))

        try:
            current, dirs, files = os.walk(path).next()
        except:
            return

    if len (dirs) == 0:
        return
   
    dirs = sorted(dirs, key=str.lower)

    flagDir = xbmc.translatePath(os.path.join(ADDON.getAddonInfo('path'), 'resources', 'flags'))

    import re
    for idx, dir in enumerate(dirs):
        valid = False
        code  = ''
        try:
            text  = getLanguage(dir) 
            code  = re.compile('<language locale="(.+?)">').search(text).group(1)
            flag  = os.path.join(flagDir, '%s.png' % code.lower())
            valid = os.path.exists(flag)
        except:
            pass

        if not valid:
            flag = getUnknownFlag(dir)
            flag = os.path.join(flagDir, '%s.png' % flag)

        menu.append([dir, idx, flag])
        
    list    = getSetting(setting)
    current = None

    if len(list) > 0:
        current = list[0]
     
    option = select.select(xbmc.getLocalizedString(21448), menu, current)

    if option < 0:
        return

    language = menu[option][0]

    if (language == current) and (len(list) == 1):
        return

    setSetting(setting, [language])
    execute('Skin.SetBool(SubtitleDownloadSet)')
    refreshSkinString(setting)


def doSetSubtitlePreferred():
    import select
    menu = []

    original = xbmc.getLocalizedString(308)
    default  = xbmc.getLocalizedString(309)

    setting = 'locale.subtitlelanguage'

    file = xbmc.translatePath(os.path.join(ADDON.getAddonInfo('path'), 'resources', 'subtitle.txt'))

    options = []
    try:        
        f       = open(file, 'r')
        options = f.readlines()
        f.close()
    except:
        return
   
    options = sorted(options, key=str.lower)

    menu.append([original, 0])
    menu.append([default,  1])

    idx = 2

    for option in options:
        exec(option)
        menu.append([option, idx])
        idx += 1

    current = getSetting(setting)

    if current == 'original':
        current = original
    elif current == 'default':
        current = default

    option = select.select(xbmc.getLocalizedString(286), menu, current)

    if option < 0:
        return

    if option == 0:
        language = 'original'
    elif option == 1:
        language = 'default'
    else:
        language = menu[option][0]

    if language == current:
        return

    setSetting(setting, language)
    execute('Skin.SetBool(SubtitlePreferredSet)')
    refreshSkinString(setting)


def doSetRegion():
    import select
    menu = []

    setting  = 'locale.country' #region

    language = getSetting('locale.language')
    text     = getLanguage(language)

    if not text:
        return

    import re

    theRegions = []

    regions = re.compile('<region name="(.+?)"').findall(text)
    for region in regions:
        theRegions.append(region)

    regions = re.compile('<locale="(.+?)">').findall(text)
    for region in regions:
        theRegions.append(region)

    theRegions.sort()

    for idx, region in enumerate(theRegions):
        menu.append([region, idx])

    if len(menu) < 1:
        return

    current = getSetting(setting)

    option = select.select(xbmc.getLocalizedString(20026), menu, current)

    if option < 0:
        return

    region = menu[option][0]

    if region == current:
        return

    setSetting(setting, region)
    execute('Skin.SetBool(RegionSet)')
    refreshSkinString(setting)


def zoom(up):
    setting = 'lookandfeel.skinzoom'
    value   = getSetting(setting)

    if (up):
        value += 2
    else:
        value -= 2

    if value > 20:
        value = -20

    if value < -20:
        value = 20    

    setSetting(setting, value)
    refreshSkinString(setting)

def refresh():
    refreshSkinString('locale.language')
    refreshSkinString('locale.subtitlelanguage')
    refreshSkinString('locale.country')
    refreshSkinString('locale.timezonecountry')
    refreshSkinString('locale.timezone')
    refreshSkinString('lookandfeel.skinzoom')
    refreshSkinString('subtitles.languages')
    refreshSkinString('subtitles.charset')

#    firmware = xbmcaddon.Addon('script.tlbb.m6').getSetting('cVersion').replace('\r', '').replace('\n', '')
#    xbmc.executebuiltin('Skin.SetString(%s,%s)' % ('firmware', firmware))

    setting = 'lookandfeel.skin'
    skin    = getSetting(setting)
    if skin:
        if skin.startswith('skin.'):
            skin = skin[5:]
        xbmc.executebuiltin('Skin.SetString(%s,%s)' % (setting, skin))


def refreshSkinString(setting):
    value = getSetting(setting)

    if isinstance(value, list):
        value = str(value[0])
    else:
        value = str(value)

    if setting == 'subtitles.charset':
        charsets = getCharsets()
        for charset in charsets:
            if value == charset[1]:
                xbmc.executebuiltin('Skin.SetString(%s,%s)' % (setting, charset[0]))
                break
        return

    if setting == 'locale.timezonecountry' and len(value) == 0:
        value = 'Default'

    if value:
        xbmc.executebuiltin('Skin.SetString(%s,%s)' % (setting, value))
    else:
        xbmc.executebuiltin('Skin.Reset(%s)' % setting)


class Image_Screen(xbmcgui.Window):
  def __init__(self,*args,**kwargs):
    global download_thread
    self.header=kwargs['header']
    self.background=kwargs['background']
    self.icon=kwargs['icon']
    self.maintext=kwargs['maintext']

    if not os.path.exists(branding_update):
        self.addControl(xbmcgui.ControlImage(0,0,1280,720, addonfolder+'resources/images/whitebg.jpg'))
#    self.addControl(xbmcgui.ControlImage(0,0,1280,720, addonfolder+'resources/images/'+self.background))
    self.addControl(xbmcgui.ControlImage(0,0,1280,720, branding_update))
    self.updateimage = xbmcgui.ControlImage(200,230,250,250, addonfolder+'resources/images/'+self.icon)
    self.addControl(self.updateimage)   
    self.updateimage.setAnimations([('conditional','effect=rotate start=0 end=360 center=auto time=3000 loop=true condition=true',)])

# Add header text
#    self.strHeader = xbmcgui.ControlLabel(350, 150, 250, 20, '', 'font14','0xFF000000')
#    self.addControl(self.strHeader)
#    self.strHeader.setLabel(self.header)
# Add description text
    if not os.path.exists(branding_update):
        self.strDescription = xbmcgui.ControlTextBox(570, 250, 600, 300, 'font14','0xFF000000')
        self.addControl(self.strDescription)
        self.strDescription.setText(self.maintext)
    
  def onAction(self, action):
    if action == ACTION_PREVIOUS_MENU or action == ACTION_HOME:
      print"ESC and HOME Disabled"

        
class MainMenu(xbmcgui.Window):
  def __init__(self,*args,**kwargs):
    self.header=kwargs['header']
    self.background=kwargs['background']
    
    if kwargs['backbutton'] != '':
        self.backbutton=kwargs['backbutton']
    else:
        self.backbutton=''
    if kwargs['nextbutton'] != '':
        self.nextbutton=kwargs['nextbutton']
    else:
        self.nextbutton=''

    self.backbuttonfunction=kwargs['backbuttonfunction']
    self.nextbuttonfunction=kwargs['nextbuttonfunction']

    if kwargs['selectbutton'] != '':
        self.selectbutton=kwargs['selectbutton']
    else:
        self.selectbutton=''
    self.toggleup=kwargs['toggleup']
    self.toggledown=kwargs['toggledown']
    self.selectbuttonfunction=kwargs['selectbuttonfunction']
    self.toggleupfunction=kwargs['toggleupfunction']
    self.toggledownfunction=kwargs['toggledownfunction']
    self.maintext=kwargs['maintext']

    if kwargs['noconnectionbutton'] != '':
        self.noconnectionbutton=kwargs['noconnectionbutton']
    else:
        self.noconnectionbutton=''

    self.noconnectionfunction=kwargs['noconnectionfunction']
# Add background images
    self.addControl(xbmcgui.ControlImage(0,0,1280,720, addonfolder+'resources/images/smoke_background.jpg'))
    self.addControl(xbmcgui.ControlImage(0,0,1280,720, addonfolder+'resources/images/'+self.background))
    self.addControl(xbmcgui.ControlImage(0,0,1280,720, 'special://home/media/branding/branding.png'))

# Add next button
    self.button1 = xbmcgui.ControlButton(910, 600, 225, 35, self.nextbutton,font='font13',alignment=2,focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
    self.addControl(self.button1)

# Add back button
    if self.backbutton != '':
        self.button2 = xbmcgui.ControlButton(400, 600, 225, 35, self.backbutton,font='font13',alignment=2,focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
        self.addControl(self.button2)

# Add buttons - if toggle buttons blank then just use one button
    if self.toggleup=='':
        if self.noconnectionbutton=='':
            self.button0 = xbmcgui.ControlButton(910, 480, 225, 35, self.selectbutton,font='font13',alignment=2,focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
        else:
            if ipaddress != '0':
                self.button0 = xbmcgui.ControlButton(910, 480, 225, 35, self.selectbutton,font='font13',alignment=2,focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
            elif ipaddress == '0':
                self.button0 = xbmcgui.ControlButton(910, 480, 225, 35, self.noconnectionbutton,font='font13',alignment=2,focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
        self.addControl(self.button0)
        self.button0.controlDown(self.button1)
        self.button0.controlRight(self.button1)
        self.button0.controlUp(self.button1)
        if self.backbutton != '':
            self.button0.controlLeft(self.button2)
    else:
        self.toggleupbutton = xbmcgui.ControlButton(1000, 480, 35, 35, '', focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
        self.toggledownbutton = xbmcgui.ControlButton(1000, 500, 35, 35, '', focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
        self.addControl(self.toggleupbutton)
        self.addControl(self.toggledownbutton)
        self.strToggleUp = xbmcgui.ControlLabel(380, 50, 250, 20, '', 'font13','0xFFFFFFFF')
        self.strToggleDown = xbmcgui.ControlLabel(380, 50, 250, 20, '', 'font13','0xFFFFFFFF')
        self.addControl(self.strToggleUp)
        self.addControl(self.strToggleDown)
        self.strToggleUp.setLabel(self.toggleup)
        self.strToggleDown.setLabel(self.toggledown)
        self.toggleupbutton.controlDown(self.toggledownbutton)
        if self.backbutton != '':
            self.toggleupbutton.controlLeft(self.button2)
            self.toggledownbutton.controlLeft(self.button2)
        self.toggledownbutton.controlUp(self.toggleupbutton)
        self.toggledownbutton.controlDown(self.button1)
        
    if self.toggleup=='':
        self.setFocus(self.button1)
    else:
        self.setFocus(self.toggleupbutton)

    if self.backbutton != '':
        self.button1.controlLeft(self.button2)
        self.button1.controlRight(self.button2)
        self.button2.controlRight(self.button1)
        self.button2.controlLeft(self.button1)
    if self.toggleup=='':
        self.button1.controlUp(self.button0)
        if self.backbutton != '':
            self.button2.controlUp(self.button0)
    else:
        self.button1.controlUp(self.toggledownbutton)
        if self.backbutton != '':
            self.button2.controlUp(self.toggledownbutton)
        

# Add header text
    self.strHeader = xbmcgui.ControlLabel(380, 50, 250, 20, '', 'font14','0xFFFFFFFF')
    self.addControl(self.strHeader)
    self.strHeader.setLabel(self.header)
# Add internet warning text (only visible if not connected)
    if ipaddress == '0':
        self.strWarning = xbmcgui.ControlTextBox(830, 300, 300, 200, 'font13','0xFFFF0000')
        self.addControl(self.strWarning)
        self.strWarning.setText('No internet connection.[CR]To be able to get the most out of this device and set options like this you must be connected to the web. Please insert your ethernet cable or setup your Wi-Fi.')
# Add description text
    self.strDescription = xbmcgui.ControlTextBox(830, 130, 300, 300, 'font14','0xFF000000')
    self.addControl(self.strDescription)
    self.strDescription.setText(self.maintext)
    
  def onAction(self, action):
    if action == ACTION_PREVIOUS_MENU and self.selectbutton == 'Register':
      self.close()
      Skip_Registration()
 
  def onControl(self, control):
    if control == self.button0:
        if ipaddress != '0' or self.noconnectionbutton=='':
            exec self.selectbuttonfunction
        else:
            exec self.noconnectionfunction
    if control == self.button1:
      exec self.nextbuttonfunction
    if self.backbutton != '':
        if control == self.button2:
          exec self.backbuttonfunction

  def message(self, message):
    dialog = xbmcgui.Dialog()
    dialog.ok(" My message title", message) 

class MainMenuThreeItems(xbmcgui.Window):
  def __init__(self,*args,**kwargs):
    self.header=kwargs['header']
    self.background=kwargs['background']
    
    if kwargs['backbutton']!='':
        self.backbutton=kwargs['backbutton']
    else:
        self.backbutton=''
    if kwargs['nextbutton']!='':
        self.nextbutton=kwargs['nextbutton']
    else:
        self.nextbutton=''
    
    self.backbuttonfunction=kwargs['backbuttonfunction']
    self.nextbuttonfunction=kwargs['nextbuttonfunction']

    if kwargs['optionbutton1']!='':
        self.optionbutton1=kwargs['optionbutton1']
    else:
        self.optionbutton1=''
    if kwargs['optionbutton2']!='':
        self.optionbutton2=kwargs['optionbutton2']
    else:
        self.optionbutton2=''
    if kwargs['optionbutton3']!='':
       self.optionbutton3=kwargs['optionbutton3']
    else:
        self.optionbutton3=''

    self.maintext=ADDON.getLocalizedString(kwargs['maintext'])
    self.option1function=kwargs['option1function']
    self.option2function=kwargs['option2function']
    self.option3function=kwargs['option3function']
# Add background images
    self.addControl(xbmcgui.ControlImage(0,0,1280,720, addonfolder+'resources/images/smoke_background.jpg'))
    self.addControl(xbmcgui.ControlImage(0,0,1280,720, addonfolder+'resources/images/'+self.background))
    self.addControl(xbmcgui.ControlImage(0,0,1280,720, 'special://home/media/branding/branding.png'))
    if self.nextbutton != '':
        self.button1 = xbmcgui.ControlButton(910, 600, 225, 35, self.nextbutton,font='font13',alignment=2,focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
        self.addControl(self.button1)
    if self.backbutton != '':
        self.button2 = xbmcgui.ControlButton(400, 600, 225, 35, self.backbutton,font='font13',alignment=2,focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
        self.addControl(self.button2)

    self.button0 = xbmcgui.ControlButton(910, 400, 225, 35, self.optionbutton1,font='font13',alignment=2,focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
    self.button3 = xbmcgui.ControlButton(910, 440, 225, 35, self.optionbutton2,font='font13',alignment=2,focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
    self.button4 = xbmcgui.ControlButton(910, 480, 225, 35, self.optionbutton3,font='font13',alignment=2,focusTexture=addonfolder+'resources/images/button-focus.png',noFocusTexture=addonfolder+'resources/images/non-focus.jpg')
    self.addControl(self.button0)
    self.addControl(self.button3)
    self.addControl(self.button4)
    self.button0.controlDown(self.button3)
    self.button3.controlDown(self.button4)
    self.setFocus(self.button1)
    self.button3.controlUp(self.button0)
    self.button4.controlUp(self.button3)
    if self.nextbutton != '':
        self.button0.controlUp(self.button1)
        self.button3.controlRight(self.button1)
        self.button4.controlDown(self.button1)
        self.button0.controlRight(self.button1)
        self.button4.controlRight(self.button1)
        self.button1.controlLeft(self.button2)
        self.button1.controlRight(self.button2)
        self.button1.controlDown(self.button0)
        self.button1.controlUp(self.button4)
    if self.backbutton != '':
        self.button0.controlLeft(self.button2)
        self.button3.controlLeft(self.button2)
        self.button2.controlRight(self.button1)
        self.button2.controlLeft(self.button1)
        self.button2.controlUp(self.button4)
        self.button4.controlLeft(self.button2)

# Add header text
    self.strHeader = xbmcgui.ControlLabel(380, 50, 250, 20, '', 'font14','0xFFFFFFFF')
    self.addControl(self.strHeader)
    self.strHeader.setLabel(self.header)
# Add description text
    self.strDescription = xbmcgui.ControlTextBox(830, 130, 300, 300, 'font14','0xFF000000')
    self.addControl(self.strDescription)
    self.strDescription.setText(self.maintext)
    
  def onAction(self, action):
    if action == ACTION_PREVIOUS_MENU and 'Register' in self.header:
      self.close()

  def onControl(self, control):
    if control == self.button0:
      exec self.option1function
    if self.nextbutton != '':
        if control == self.button1:
            exec self.nextbuttonfunction
    if self.nextbutton != '':
        if control == self.button2:
            exec self.backbuttonfunction
    if control == self.button3:
      exec self.option2function
    if control == self.button4:
      exec self.option3function

def SelectLanguage():
    mydisplay = MainMenu(
        header=ADDON.getLocalizedString(30003),
        background='language1.png',
        backbutton='',
        nextbutton=ADDON.getLocalizedString(30002),      
        backbuttonfunction='',
        nextbuttonfunction='self.close();Check_skins("language")',
        selectbutton=ADDON.getLocalizedString(30004),
        toggleup='',
        toggledown='',
        selectbuttonfunction="doSetLanguage();self.close();xbmc.executebuiltin('RunScript('+addonfolder+'skincontrol.py)')",
        toggleupfunction='',
        toggledownfunction='',
        maintext=ADDON.getLocalizedString(30005),
        noconnectionbutton='',
        noconnectionfunction=""
        )        
    mydisplay .doModal()
    del mydisplay

def SelectRegion():
    mydisplay = MainMenuThreeItems(
        header=ADDON.getLocalizedString(30006),
        background='region1.png',
        backbutton=ADDON.getLocalizedString(30001),
        nextbutton=ADDON.getLocalizedString(30002),
        backbuttonfunction='self.close();Check_skins("region")',
        nextbuttonfunction='self.close();SelectResolution()',
        optionbutton1=ADDON.getLocalizedString(30007),
        optionbutton2=ADDON.getLocalizedString(30008),
        optionbutton3=ADDON.getLocalizedString(30009),
        option1function="doSetRegion()",
        option2function="doSetTZCountry()",
        option3function="doSetTZ()",
        maintext=ADDON.getLocalizedString(30010),
        )
    mydisplay .doModal()
    del mydisplay

def SelectResolution():
    mydisplay = MainMenu(
        header=ADDON.getLocalizedString(30011),
        background='resolution1.png',
        backbutton=ADDON.getLocalizedString(30001),
        nextbutton=ADDON.getLocalizedString(30002),
        backbuttonfunction='self.close();SelectRegion()',
        nextbuttonfunction='self.close();SelectZoom()',
        selectbutton=ADDON.getLocalizedString(30011),
        toggleup='',
        toggledown='',
        selectbuttonfunction="RESOLUTION()",
        toggleupfunction='',
        toggledownfunction='',
        maintext=ADDON.getLocalizedString(30012),
        noconnectionbutton='',
        noconnectionfunction=""
        )
    mydisplay .doModal()
    del mydisplay

def SelectZoom():
    mydisplay = MainMenu(
        header=ADDON.getLocalizedString(30013),
        background='zoom1.png',
        backbutton=ADDON.getLocalizedString(30001),
        nextbutton=ADDON.getLocalizedString(30002),
        backbuttonfunction='self.close();SelectResolution()',
        nextbuttonfunction='self.close();SelectWeather()',
        selectbutton=ADDON.getLocalizedString(30014),
        toggleup='',
        toggledown='',
        selectbuttonfunction="xbmc.executebuiltin('ActivateWindow(screencalibration)')",
        toggleupfunction='',
        toggledownfunction='',
        maintext=ADDON.getLocalizedString(30015),
        noconnectionbutton='',
        noconnectionfunction=""
        )
    mydisplay .doModal()
    del mydisplay

def SelectWeather():
    mydisplay = MainMenu(
        header=ADDON.getLocalizedString(30016),
        background='weather1.png',
        backbutton=ADDON.getLocalizedString(30001),
        nextbutton=ADDON.getLocalizedString(30002),
        backbuttonfunction='self.close();SelectZoom()',
        nextbuttonfunction='self.close();InstallLocalContent()',
        selectbutton=ADDON.getLocalizedString(30017),
        toggleup='',
        toggledown='',
        selectbuttonfunction="xbmc.executebuiltin(xbmcaddon.Addon(id='weather.yahoo').openSettings(sys.argv[0]))",
        toggleupfunction='',
        toggledownfunction='',
        maintext=ADDON.getLocalizedString(30018),
        noconnectionbutton=ADDON.getLocalizedString(30019),
        noconnectionfunction="xbmc.executebuiltin('ActivateWindow(home)');xbmc.executebuiltin('RunAddon(service.openelec.settings)');xbmc.executebuiltin('RunAddon(script.openwindow)')"
        )
    mydisplay .doModal()
    del mydisplay

def SelectSkin():
    speedtest=0
    mydisplay = MainMenu(
        header=ADDON.getLocalizedString(30020),
        background='skins1.png',
        backbutton=ADDON.getLocalizedString(30001),
        nextbutton=ADDON.getLocalizedString(30002),
        backbuttonfunction='self.close();SelectLanguage()',
        nextbuttonfunction='self.close();SelectRegion()',
        selectbutton=ADDON.getLocalizedString(30021),
        toggleup='',
        toggledown='',
        selectbuttonfunction="doSetSkin()",
        toggleupfunction='',
        toggledownfunction='',
        maintext=ADDON.getLocalizedString(30022),
        noconnectionbutton=ADDON.getLocalizedString(30019),
        noconnectionfunction="xbmc.executebuiltin('ActivateWindow(home)');xbmc.executebuiltin('RunAddon(service.openelec.settings)');xbmc.executebuiltin('RunAddon(script.openwindow)')"
        )
    mydisplay .doModal()
    del mydisplay
    
def InstallKeyword():
    mydisplay = MainMenu(
        header=ADDON.getLocalizedString(30023),
        background='keywords1.png',
        backbutton=ADDON.getLocalizedString(30001),
        nextbutton=ADDON.getLocalizedString(30002),
        backbuttonfunction='self.close();InstallLocalContent()',
        nextbuttonfunction='self.close();FINISH()',
        selectbutton=ADDON.getLocalizedString(30024),
        toggleup='',
        toggledown='',
        selectbuttonfunction="KEYWORD_SEARCH()",
        toggleupfunction='',
        toggledownfunction='',
        maintext=ADDON.getLocalizedString(30025),
        noconnectionbutton=ADDON.getLocalizedString(30019),
        noconnectionfunction="xbmc.executebuiltin('ActivateWindow(home)');xbmc.executebuiltin('RunAddon(service.openelec.settings)');xbmc.executebuiltin('RunAddon(script.openwindow)')"
        )
    mydisplay .doModal()
    del mydisplay

def InstallLocalContent():
    mydisplay = MainMenuThreeItems(
        header=ADDON.getLocalizedString(30026),
        background='localcontent1.png',
        backbutton=ADDON.getLocalizedString(30001),
        nextbutton=ADDON.getLocalizedString(30002),
        backbuttonfunction='self.close();SelectWeather()',
        nextbuttonfunction='self.close();InstallKeyword()',
        optionbutton1=ADDON.getLocalizedString(30027),
        optionbutton2=ADDON.getLocalizedString(30028),
        optionbutton3=ADDON.getLocalizedString(30029),
        option1function="ADDMUSIC()",
        option2function="ADDPHOTOS()",
        option3function="ADDVIDEOS()",
        maintext=ADDON.getLocalizedString(30030),
        )
    mydisplay .doModal()
    del mydisplay
    
def Verify(mode):
    mydisplay = MainMenu(
        header=ADDON.getLocalizedString(30062),
        background='register.png',
        backbutton=ADDON.getLocalizedString(30001),
        nextbutton=ADDON.getLocalizedString(30002),
        backbuttonfunction='self.close();SelectLanguage()',
        nextbuttonfunction='self.close();Get_Activation("check")',
        selectbutton=ADDON.getLocalizedString(30063),
        toggleup='',
        toggledown='',
        selectbuttonfunction="self.close();Get_Activation('normal')",
        toggleupfunction='',
        toggledownfunction='',
        maintext=ADDON.getLocalizedString(30064),
        noconnectionbutton=ADDON.getLocalizedString(30019),
        noconnectionfunction="xbmc.executebuiltin('ActivateWindow(home)');xbmc.executebuiltin('RunAddon(service.openelec.settings)');xbmc.executebuiltin('RunAddon(script.openwindow)')"
        )
    mydisplay .doModal()
    del mydisplay

def Get_Activation(mode):
    if mode == 'check':
        if Check_Status():
            statusinfo = ADDON.getLocalizedString(30065)
        else:
            statusinfo = ADDON.getLocalizedString(30066)
    else:
        statusinfo = ''
        registration_link = mode
    mydisplay = MainMenu(
        header=ADDON.getLocalizedString(30062),
        background='register.png',
        backbutton=ADDON.getLocalizedString(30067),
        nextbutton=ADDON.getLocalizedString(30002),
        backbuttonfunction='self.close();Skip_Registration()',
        nextbuttonfunction='self.close();Check_Status()',
        selectbutton=ADDON.getLocalizedString(30068),
        toggleup='',
        toggledown='',
        selectbuttonfunction="self.close();Check_Status()",
        toggleupfunction='',
        toggledownfunction='',
        maintext=ADDON.getLocalizedString(30069)+registration_link+'[/COLOR]'+statusinfo,
        noconnectionbutton='ADDON.getLocalizedString(30019)',
        noconnectionfunction="xbmc.executebuiltin('ActivateWindow(home)');xbmc.executebuiltin('RunAddon(service.openelec.settings)');xbmc.executebuiltin('RunAddon(script.openwindow)')"
        )
    mydisplay .doModal()
    del mydisplay

def Skip_Registration():
    print"Skip_Registration"
    mydisplay = MainMenu(
        header=ADDON.getLocalizedString(30067),
        background='donotregister.png',
        backbutton=ADDON.getLocalizedString(30070),
        nextbutton=ADDON.getLocalizedString(30071),
        backbuttonfunction='xbmc.executebuiltin("Skin.SetString(Branding,off)");self.close()',
        nextbuttonfunction='Check_Status()',
        selectbutton=ADDON.getLocalizedString(30072),
        toggleup='',
        toggledown='',
        selectbuttonfunction="Registration_Details()",
        toggleupfunction='',
        toggledownfunction='',
        maintext=ADDON.getLocalizedString(30073),
        noconnectionbutton=ADDON.getLocalizedString(30019),
        noconnectionfunction="xbmc.executebuiltin('ActivateWindow(home)');xbmc.executebuiltin('RunAddon(service.openelec.settings)');xbmc.executebuiltin('RunAddon(script.openwindow)')"
        )
    mydisplay .doModal()
    del mydisplay
    
def Update_Screen():
    mydisplay = Image_Screen(
        header='Update In Progress',
        background='register.png',
        icon='update_software.png',
        maintext=ADDON.getLocalizedString(30074),
        )
    mydisplay .doModal()
    del mydisplay

def Check_Activation():
    if Check_Status():
        Check_skins("verify")
    else:
        Verify('error')
    
def Registration_Details():
    print"Registration_Details"
    Text_Boxes(ADDON.getLocalizedString(30079),ADDON.getLocalizedString(30080))

def Check_skins(mode):
    if mode == 'language':
        if not os.path.exists(os.path.join(addonfolder,'resources','skinlist.txt')):
            SelectRegion()
        else:
            SelectSkin()
    if mode == 'region':
        if not os.path.exists(os.path.join(addonfolder,'resources','skinlist.txt')):
            SelectLanguage()
        else:
            SelectSkin()
        
def ADDMUSIC():
        xbmc.executebuiltin('ActivateWindow(musicfiles,return)')
        xbmc.executebuiltin('Action(PageDown)')
        xbmc.executebuiltin('Action(Select)')

def ADDPHOTOS():
        xbmc.executebuiltin('ActivateWindow(pictures,return)')
        xbmc.executebuiltin('Action(PageDown)')
        xbmc.executebuiltin('Action(Select)')

def ADDVIDEOS():
        xbmc.executebuiltin('ActivateWindow(video,files,return)')
        xbmc.executebuiltin('Action(PageDown)')
        xbmc.executebuiltin('Action(Select)')

def RESOLUTION():
        print"RESOLUTION"
        xbmc.executebuiltin('ActivateWindow(systemsettings,return)')
        xbmc.executebuiltin('Action(Right)')
        xbmc.executebuiltin('Action(Select)')

def KEYWORD_SEARCH():
        print"KEYWORD_SEARCH"
        downloadurl=''
        url='http://urlshortbot.com/venztech'
        keyword      =  SEARCH(ADDON.getLocalizedString(30031))
        downloadurl  =  url+keyword
        if not os.path.exists(venzpath):
            os.makedirs(venzpath)
        if keyword !='':
            try:
                dp.create(ADDON.getLocalizedString(30032),ADDON.getLocalizedString(30033),'', ADDON.getLocalizedString(30034))
                downloader.download(downloadurl,lib)
                dp.update(0,"", ADDON.getLocalizedString(30035))
                if zipfile.is_zipfile(lib):
                        dialog.ok(ADDON.getLocalizedString(30036), "",ADDON.getLocalizedString(30037))
                else:
                    if os.path.getsize(lib) > 100000:
                        dp.create(ADDON.getLocalizedString(30038),ADDON.getLocalizedString(30039),'', ADDON.getLocalizedString(30034))
                        os.rename(lib,restore_dir+'20150815123607.tar')
                        dp.update(0,"", ADDON.getLocalizedString(30040))
                        dp.close()
                        xbmc.executebuiltin('reboot')
                    else:
                        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30041),ADDON.getLocalizedString(30042),ADDON.getLocalizedString(30043))
            except:
                xbmcgui.Dialog().ok(ADDON.getLocalizedString(30041),ADDON.getLocalizedString(30042),ADDON.getLocalizedString(30043))       

def SEARCH(searchtext):
        print"SEARCH"
        search_entered = ''
        keyboard = xbmc.Keyboard(search_entered,searchtext)
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_entered =  keyboard.getText() .replace(' ','%20')
            if search_entered == None:
                return False          
        return search_entered

def FINISH():
    print"FINISH"
    if skin == 'skin.confluence' and os.path.exists(os.path.join(addonfolder,'resources','skinlist.txt')):
        choice=dialog.yesno(ADDON.getLocalizedString(30044),ADDON.getLocalizedString(30045),yeslabel=ADDON.getLocalizedString(30046),nolabel=ADDON.getLocalizedString(30047))
        if choice==0:
            SelectSkin()
    if os.path.exists(lib):
        dialog.ok(ADDON.getLocalizedString(30048),ADDON.getLocalizedString(30049),ADDON.getLocalizedString(30050))
        if zipfile.is_zipfile(lib):
            try:
                dp.create(ADDON.getLocalizedString(30051),ADDON.getLocalizedString(30052),' ', ' ')
                extract.all(lib,rootfolder,dp)
                dp.close()
                newguifile = os.path.join(HOME,'newbuild')
                if not os.path.exists(newguifile):
                    os.makedirs(newguifile)
            except:
                dialog.ok(ADDON.getLocalizedString(30053),ADDON.getLocalizedString(30054))
        os.remove(lib)
        Remove_Textures()
        dialog.ok(ADDON.getLocalizedString(30055),ADDON.getLocalizedString(30056),ADDON.getLocalizedString(30057))
        KILL_KODI()

        
def Download_Function(url):
    urllib.urlretrieve(url,lib)
    
    
def Download_Extract(url,video):
    global download_thread
    global endtime
    if not os.path.exists(RunWizard):
        os.makedirs(RunWizard)
    download_thread = threading.Thread(target=Download_Function, args=[url])
    updatescreen_thread = threading.Thread(target=Update_Screen)
    try:
        download_thread.start()
        starttime = datetime.datetime.now()
        print"###Download Started"
    except:
        dialog.ok('Error','Unable to download updates from server. Please try opening a web browser on your PC to make sure your internet is working correctly. Click OK to try again.')
        if os.path.exists(addondata):
            shutil.rmtree(addondata)
        xbmc.executebuiltin('reboot')
    try:
        yt.PlayVideo(video)
    except:
        pass
    while xbmc.Player().isPlaying():
        xbmc.sleep(500)
    updatescreen_thread.start()
    while download_thread.isAlive():
        xbmc.sleep(500)
    endtime   = datetime.datetime.fromtimestamp(os.path.getmtime(lib))
    timediff  = endtime-starttime
    libsize   = os.path.getsize(lib) / (128*1024.0)
    timediff = str(timediff).replace(':','')
    speed = libsize / float(timediff)
    writefile = open(timepath, mode='w+')
    writefile.write(str(speed))
    writefile.close()

    if os.path.exists(lib) and zipfile.is_zipfile(lib):
        zin = zipfile.ZipFile(lib, 'r')
        zin.extractall(rootfolder)
        try:
            os.remove(lib)
        except:
            print"### Failed to remove temp file"
        Remove_Textures()
        print"### Removed textures"
        KILL_KODI()

def Check_Status():
    print"Check_Status"
# Function to check activation status of the unit
    url   = ''
    video = ''
    status = Activate()
    if '~' in status:
        url,video = status.split('~')
        url = encryptme('d',url)
        video = encryptme('d',video)
    else:
        try:
            url = encryptme('d',status)
        except:
            pass
# If activation sends back vanilla
    if  url==encryptme('d','595d515c110b0d1804'):
        mode = 'quit'

# If activation sends back registration
    if encryptme('d','5b6767632d2222675f555521605804060d1006') in url:
        if '~' in status and not os.path.exists(xbmc.translatePath(os.path.join(HOME,'media','branding'))):
            try:
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                urllib.urlretrieve(video,lib)
                xbmc.executebuiltin("Dialog.Close(busydialog)")
            except:
                pass
            if os.path.exists(lib) and zipfile.is_zipfile(lib):
                zin = zipfile.ZipFile(lib, 'r')
                zin.extractall(rootfolder)
                zin.close()
                try:
                    os.remove(lib)
                except:
                    pass
        Get_Activation(url)
                
# If download URL in activation
    elif encryptme('d','5e6a6a663025250b1c0a0506') in url:
        Download_Extract(url,video)
        
# If user has no internet on first boot and wants to use Kodi vanilla
    elif status == 'back':
        try:
            shutil.rmtree(addondata)
        except:
            pass
        xbmc.executebuiltin('reboot')

        
def KILL_KODI():
    print"KILL_KODI"
    if xbmc.getCondVisibility('system.platform.windows'):
        try:
            os.system('@ECHO off')
            os.system('TASKKILL /im Kodi.exe /f')
        except:
            pass
        try:
            os.system('@ECHO off')
            os.system('tskill Kodi.exe')
        except:
            pass
        try:
            os.system('@ECHO off')
            os.system('tskill XBMC.exe')
        except:
            pass
        try:
            os.system('@ECHO off')
            os.system('TASKKILL /im XBMC.exe /f')
        except:
            pass
    elif xbmc.getCondVisibility('system.platform.osx'):
        try:
            os.system('killall -9 XBMC')
        except:
            pass
        try:
            os.system('killall -9 Kodi')
        except:
            pass
    else:
#    elif xbmc.getCondVisibility('system.platform.linux'):
        try:
            os.system('killall XBMC')
        except:
            pass
        try:
            os.system('killall Kodi')
        except:
            pass
        try:
            os.system('killall -9 xbmc.bin')
        except:
            pass
        try:
            os.system('killall -9 kodi.bin')
        except:
            pass
 #   else: #ATV
        try:
            os.system('killall AppleTV')
        except:
            pass
        try:
            os.system('sudo initctl stop kodi')
        except:
            pass
        try:
            os.system('sudo initctl stop xbmc')
        except:
            pass
#    elif xbmc.getCondVisibility('system.platform.android'):
        try:
            os.system('adb shell am force-stop org.xbmc.kodi')
        except:
            pass
        try:
            os.system('adb shell am force-stop org.kodi')
        except:
            pass
        try:
            os.system('adb shell am force-stop org.xbmc.xbmc')
        except:
            pass
        try:
            os.system('adb shell am force-stop org.xbmc')
        except:
            pass        
        try:
            os.system('adb shell kill org.xbmc.kodi')
        except:
            pass
        try:
            os.system('adb shell kill org.kodi')
        except:
            pass
        try:
            os.system('adb shell kill org.xbmc.xbmc')
        except:
            pass
        try:
            os.system('adb shell kill org.xbmc')
        except:
            pass        
        try:
            os.system('Process.killProcess(android.os.Process.org.xbmc,kodi());')
        except:
            pass
        try:
            os.system('Process.killProcess(android.os.Process.org.kodi());')
        except:
            pass
        try:
            os.system('Process.killProcess(android.os.Process.org.xbmc.xbmc());')
        except:
            pass
        try:
            os.system('Process.killProcess(android.os.Process.org.xbmc());')
        except:
            pass
        dialog.ok('Attempting to use advanced task killer apk','If you have the advanced task killer apk installed please click the big button at the top which says "KILL selected apps". Click "OK" then "Kill selected apps. Please be patient while your system updates the necessary files and your skin will automatically switch once fully updated.')
        try:
            xbmc.executebuiltin('StartAndroidActivity(com.rechild.advancedtaskkiller)')
        except:
            pass

def Remove_Textures():
    textures  =  xbmc.translatePath('special://home/userdata/Database/Textures13.db')
    try:
        dbcon = database.connect(textures)
        dbcur = dbcon.cursor()
        dbcur.execute("DROP TABLE IF EXISTS path")
        dbcur.execute("VACUUM")
        dbcon.commit()
        dbcur.execute("DROP TABLE IF EXISTS sizes")
        dbcur.execute("VACUUM")
        dbcon.commit()
        dbcur.execute("DROP TABLE IF EXISTS texture")
        dbcur.execute("VACUUM")
        dbcon.commit()
        dbcur.execute("""CREATE TABLE path (id integer, url text, type text, texture text, primary key(id))""")
        dbcon.commit()
        dbcur.execute("""CREATE TABLE sizes (idtexture integer,size integer, width integer, height integer, usecount integer, lastusetime text)""")
        dbcon.commit()
        dbcur.execute("""CREATE TABLE texture (id integer, url text, cachedurl text, imagehash text, lasthashcheck text, PRIMARY KEY(id))""")
        dbcon.commit()
    except:
        pass
    shutil.rmtree(thumbnails)

def CPU_Check():
    version=str(xbmc_version[:2])
    if version < 14:
        logfile = os.path.join(log_path, 'xbmc.log')
    
    else:
        logfile = os.path.join(log_path, 'kodi.log')

    filename    = open(logfile, 'r')
    logtext     = filename.read()
    filename.close()

    CPUmatch    = re.compile('Host CPU: (.+?) available').findall(logtext)
    CPU         = CPUmatch[0] if (len(CPUmatch) > 0) else ''
    return CPU.replace(' ','%20')


def Build_Info():
    version=str(xbmc_version[:2])
    if version < 14:
        logfile = os.path.join(log_path, 'xbmc.log')
    
    else:
        logfile = os.path.join(log_path, 'kodi.log')

    filename    = open(logfile, 'r')
    logtext     = filename.read()
    filename.close()

    Buildmatch  = re.compile('Running on (.+?)\n').findall(logtext)
    Build       = Buildmatch[0] if (len(Buildmatch) > 0) else ''
    return Build.replace(' ','%20')


def getMacAddress(protocol):
    if sys.platform == 'win32': 
        for line in os.popen("ipconfig /all"): 
            if line.lstrip().startswith('Physical Address'): 
                mac = line.split(':')[1].strip().replace('-',':')
                break 

    if xbmc.getCondVisibility('System.Platform.Android'):
        if protcol == 'wifi':
            readfile = open('/sys/class/net/wlan0/address', mode='r')
        else:
            readfile = open('/sys/class/net/eth0/address', mode='r')
        mac = readfile.read()
        mac = mac[:17]
        readfile.close()

    else:
        if protocol == 'wifi':
            for line in os.popen("/sbin/ifconfig"): 
                if line.find('wlan0') > -1: 
                    mac = line.split()[4] 
                    break
        else:
           for line in os.popen("/sbin/ifconfig"): 
                if line.find('eth0') > -1: 
                    mac = line.split()[4] 
                    break
    return str(mac)

def Text_Boxes(heading,anounce):
  class TextBox():
    WINDOW=10147
    CONTROL_LABEL=1
    CONTROL_TEXTBOX=5
    def __init__(self,*args,**kwargs):
      xbmc.executebuiltin("ActivateWindow(%d)" % (self.WINDOW, )) # activate the text viewer window
      self.win=xbmcgui.Window(self.WINDOW) # get window
      xbmc.sleep(500) # give window time to initialize
      self.setControls()
    def setControls(self):
      self.win.getControl(self.CONTROL_LABEL).setLabel(heading) # set heading
      try:
        f=open(anounce); text=f.read()
      except:
        text=anounce
      self.win.getControl(self.CONTROL_TEXTBOX).setText(str(text))
      return
  TextBox()
  while xbmc.getCondVisibility('Window.IsVisible(10147)'):
      xbmc.sleep(500)
    
def Activate():
    counter = 0
    success = 0
    try:
        wifimac = getMacAddress('wifi')
    except:
        wifimac = 'Unknown'
    try:
        ethmac  = getMacAddress('eth0')
    except:
        ethmac  = 'Unknown'
    try:
        cpu     = CPU_Check()
    except:
        cpu     = 'Unknown'
    try:
        build   = Build_Info()
    except:
        build   = 'Unknown'
    urlparams = wifimac+'&'+cpu+'&'+build+'&'+ethmac.replace(' ','%20')
    while counter <3 and success == 0:
        try:
            counter += 1
            link = Open_URL(encryptme('d','4a5656521c1111564e4444104f471123464610524a52215a1f0e16141e04')+encryptme('e',urlparams))
            success = 1
        except:
            dialog.ok(ADDON.getLocalizedString(30075),ADDON.getLocalizedString(30076))
    if success == 1:
        return link
    else:
        choice = dialog.yesno(ADDON.getLocalizedString(30075),ADDON.getLocalizedString(30077))
        if choice == 1:
            dialog.ok(ADDON.getLocalizedString(30075),ADDON.getLocalizedString(30078))
            try:
                shutil.rmtree(addondata)
            except:
                pass
            return '595d515c110b0d1804'
        else:
            return 'back'

def Open_URL(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent' , 'Mozilla/5.0 (Windows; U; Windows NT 10.0; WOW64; Windows NT 5.1; en-GB; rv:1.9.0.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36 Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    link     = response.read()
    response.close()
    return link.replace('\r','').replace('\n','').replace('\t','')

def encryptme(mode, message):
    if mode == 'e':
        import random
        count = 0
        finaltext = ''
        while count < 4:
            count += 1
            randomnum = random.randrange(1, 31)
            hexoffset = hex(randomnum)[2:]
            if len(hexoffset)==1:
                hexoffset = '0'+hexoffset
            finaltext = finaltext+hexoffset
        randomchar = random.randrange(1,4)
        if randomchar == 1: finaltext = finaltext+'0A'
        if randomchar == 2: finaltext = finaltext+'04'
        if randomchar == 3: finaltext = finaltext+'06'
        if randomchar == 4: finaltext = finaltext+'08'
        key1    = finaltext[-2:]
        key2    = int(key1,16)
        hexkey  = finaltext[-key2:-(key2-2)]
        key     = -int(hexkey,16)

# enctrypt/decrypt the message
        translated = ''
        finalstring = ''
        for symbol in message:
            num = ord(symbol)
            num2 = int(num) + key
            hexchar = hex(num2)[2:]
            if len(hexchar)==1:
                hexchar = '0'+hexchar
            finalstring = str(finalstring)+str(hexchar)
        return finalstring+finaltext
    else:
        key1    = message[-2:]
        key2    = int(key1,16)
        hexkey  = message[-key2:-(key2-2)]
        key     = int(hexkey,16)
        message = message [:-10]
        messagearray = [message[i:i+2] for i in range(0, len(message), 2)]
        numbers = [ int(x,16)+key for x in messagearray ]
        finalarray = [ str(unichr(x)) for x in numbers ]
        finaltext = ''.join(finalarray)
        return finaltext.encode('utf-8')

###### Main Script Starts Here ######
xmlfile = binascii.unhexlify('6164646f6e2e786d6c')
addonxml = '/usr/share/kodi/addons/script.openwindow/addon.xml'
if not os.path.exists(addonxml):
    addonxml = xbmc.translatePath(os.path.join(ADDONS,ADDONID,xmlfile))
localaddonversion = open(addonxml, mode='r')
content = file.read(localaddonversion)
file.close(localaddonversion)
localaddonvermatch = re.compile('<ref>(.+?)</ref>').findall(content)
addonversion  = localaddonvermatch[0] if (len(localaddonvermatch) > 0) else ''
localcheck = hashlib.md5(open(installfile,'rb').read()).hexdigest()
if addonversion != localcheck:
    try:
        os.remove(installfile)
    except:
        pass

mode = None
if mode == None:
    if os.path.exists(lib):
        os.remove(lib)
    Check_Status()

elif mode =='quit':
    xbmc.executebuiltin('Skin.SetString(Branding,off)')
    xbmc.executebuiltin('StopScript(script.openwindow)')
    xbmc.executebuiltin('ActivateWindow(home)')
