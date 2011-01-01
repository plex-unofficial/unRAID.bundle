from time import sleep

####################################################################################################

APPLICATIONS_PREFIX = "/applications/unraid"

NAME    = L('unRAID')
ART     = 'art-default.png'
ICON    = 'icon-default.png'
DISK_ICON = 'icon-hdd.jpg'

####################################################################################################

def Start():

    Plugin.AddPrefixHandler(APPLICATIONS_PREFIX, ApplicationsMainMenu, L('unRAID'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)
    PopupDirectoryItem.thumb = R(ICON)

####################################################################################################

def Get_unRAID_URL():
    return 'http://%s' % Prefs['unRAID_host']

####################################################################################################

def ApplicationsMainMenu():

    dir = MediaContainer(viewGroup="InfoList", noCache=True)
    
    startState = GetStartState()
    Log(startState)
    
    dir.Append(Function(DirectoryItem(DiskStatus, 'Disk Status', 'View disk status details.',
        summary=DiskStatusSummary())))
    if startState == 'STARTED':
        dir.Append(Function(PopupDirectoryItem(ConfirmSpinUp, 'Spin up', 'will immediately spin up all disks.')))
        dir.Append(Function(PopupDirectoryItem(ConfirmSpinDown, 'Spin down', 'will immediately spin down all disks.')))
        dir.Append(Function(PopupDirectoryItem(ConfirmParityCheck, 'Check Parity', subtitle=LastParityCheck())))
        dir.Append(Function(PopupDirectoryItem(ConfirmStop, 'Stop Array', 'will take the array off-line.')))
    else:
        dir.Append(Function(PopupDirectoryItem(ConfirmStart, 'Start Array', 'will bring the array on-line.')))
        dir.Append(Function(PopupDirectoryItem(ConfirmReboot, 'Restart', 'will activate a system reset.',
            summary = 'Depending on your system, it may be a few minutes before the server (and the plugin) are back online')))
        dir.Append(Function(PopupDirectoryItem(ConfirmPowerDown, 'Power Down', 'will activate a clean power down.',
            summary = 'Once the server is powered down you will need to power it up manually. There is no "power up" command in this plugin.')))

    return dir

####################################################################################################

def GetDiskStatus():
    
    disks = []
    
    url = Get_unRAID_URL() + '/main.htm'
    mainPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0)
    for status in mainPage.xpath('//table[@id="disk_table"]/tr'):
        try:
            diskName    = status.xpath('./td[1]/a')[0].text
            statusIndicator  = status.xpath('./td[1]/img')[0].get('src')
            diskStatus = ''
            if statusIndicator == 'green-on.gif':
                diskStatus = 'Spun Up'
            elif statusIndicator == 'green-blink.gif':
                diskStatus = 'Spun Down'
            elif statusIndicator == 'blue-on.gif':
                diskStatus = '???'
            elif statusIndicator == 'red-on.gif':
                diskStatus = 'Trouble'
            serial      = status.xpath('./td[2]/strong')[0].text
            diskTemp        = status.xpath('./td[3]/strong')[0].text
            diskSize        = status.xpath('./td[4]/strong')[0].text
            freeSpace        = status.xpath('./td[5]/strong')[0].text
            diskReads       = status.xpath('./td[6]/strong')[0].text
            diskWrites      = status.xpath('./td[7]/strong')[0].text
            diskErrors      = status.xpath('./td[8]/strong')[0].text
        except:
            continue
        disks.append(
                {
                    'name':diskName,
                    'status':diskStatus,
                    's/n':serial,
                    'temp':diskTemp,
                    'size':diskSize,
                    'free':freeSpace,
                    'reads':diskReads,
                    'writes':diskWrites,
                    'errors':diskErrors
                }
            )
    
    return disks

####################################################################################################

def DiskStatusSummary():
    
    summary = ''
    disks = GetDiskStatus()
    
    for disk in disks:
        summary = summary + ('Disk: '+disk['name']+'\nStatus: '+disk['status']+'\n'
        + 'Serial Number: '+disk['s/n']+'\n'+'Temp: '+disk['temp']+'\n'+'Size: '+disk['size']+'\n'
        +'Free Space: '+disk['free']+'\n'+'Reads: '+disk['reads']+'\n'+'Writes: '+disk['writes']+'\n'
        +'Errors: '+disk['errors']+'\n\n')
    
    return summary

####################################################################################################

def DiskStatus(sender):
    
    dir = MediaContainer(title2='Disk Status', noCache=True)
    
    disks = GetDiskStatus()
    
    for disk in disks:
        dir.Append(Function(DirectoryItem(DiskMenu, title=disk['name'], subtitle=disk['s/n'],
            infolabel=disk['temp'], summary='Status: '+disk['status']+'\nSize: '+disk['size']
            +'\nFree Space: '+disk['free']+'\nReads: '+disk['reads']+'\nWrites: '+disk['writes']
            +'\nErrors: '+disk['errors'], thumb=R(DISK_ICON))))
    
    return dir

####################################################################################################

def DiskMenu(sender):
    return

####################################################################################################

def GetStartState():
    
    url = Get_unRAID_URL() + '/main.htm'
    mainPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0)
    
    state = mainPage.xpath('//input[@name="startState"]')[0].get('value')
    
    return state

####################################################################################################

def ConfirmStart(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(StartArray, 'Bring array on-line?')))
    return dir

####################################################################################################

def StartArray(sender):

    url = Get_unRAID_URL() + '/update.htm?startState=STOPPED&cmdStart=Start'
    start = HTTP.Request(url).content
    
    ###allow time for array to spin up completely before trying to reload menu###
    sleep(10)
    
    return MessageContainer(NAME, L('Array is on-line.'))

####################################################################################################

def ConfirmStop(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(StopArray, 'Take array off-line?')))
    return dir

####################################################################################################

def StopArray(sender):
    
    url = Get_unRAID_URL() + '/update.htm?startState=STARTED&cmdStop=Stop'
    stop = HTTP.Request(url).content
    
    return MessageContainer(NAME, L('Array is off-line.'))

####################################################################################################

def ConfirmSpinUp(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(SpinUpArray, 'Spin up all disks?')))
    return dir
    
####################################################################################################

def SpinUpArray(sender):
    
    url = Get_unRAID_URL() + '/update.htm?startState=STARTED&cmdSpinUpAll=Spin+Up'
    spinUp = HTTP.Request(url).content
    
    return MessageContainer(NAME, L('Disks in array are spun up.'))

####################################################################################################

def ConfirmSpinDown(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(SpinDownArray, 'Spin down all disks?')))
    return dir
    
####################################################################################################

def SpinDownArray(sender):
    
    url = Get_unRAID_URL() + '/update.htm?startState=STARTED&cmdSpinDownAll=Spin+Down'
    spinDown = HTTP.Request(url).content
    
    return MessageContainer(NAME, L('Disks in array are spun down.'))

####################################################################################################

def ConfirmParityCheck(sender):
    return

####################################################################################################

def CheckParity(sender):
    return

####################################################################################################

def LastParityCheck():
    
    url = Get_unRAID_URL() + '/main.htm'
    mainPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0)
    
    lastCheck = mainPage.xpath('//form[@name="mainForm"]/table/tr[2]/td')[0].text
    #lastCheck = mainPage.xpath('//form[@name="mainForm"]/table/tr[2]/td')[2].text
    Log(lastCheck)
    
    return lastCheck

####################################################################################################

def ConfirmReboot(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(RebootArray, 'Initiate restart?')))
    return dir

####################################################################################################

def RebootArray(sender):
    
    url = Get_unRAID_URL() + '/update.htm?startState=STOPPED&reboot=Reboot'
    reboot = HTTP.Request(url).content
    
    state = 'rebooting'
    while state == 'rebooting':
        sleep(5)
        try:
            state = GetStartState()
        except:
            continue
    
    return MessageContainer(NAME, L('The server has been reset.'))

####################################################################################################

def ConfirmPowerDown(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(PowerDownArray, 'Initiate Power Down?')))
    return dir

####################################################################################################

def PowerDownArray(sender):
    
    url = Get_unRAID_URL() + '/update.htm?startState=STOPPED&shutdown=Power+down'
    powerDown = HTTP.Request(url).content
    
    return MessageContainer(NAME, L('The server has been shut down. This plugin will not function until the server has been started again.'))

####################################################################################################