from time import sleep

####################################################################################################

APPLICATIONS_PREFIX = "/applications/unraid"

NAME    = L('unRAID')
ART     = 'art-default.png'
ICON    = 'icon-default.png'
PREFS_ICON  = 'icon-prefs.png'
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
    
    try:
        startState = GetStartState()
        Log(startState)
    except:
        startState= 'OFFLINE'
    
    if startState != 'OFFLINE':
        dir.Append(Function(DirectoryItem(DiskStatus, 'Disk Status', 'View disk status details.',
            summary=DiskStatusSummary())))
        if startState == 'STARTED':
            dir.Append(Function(PopupDirectoryItem(ConfirmSpinUp, 'Spin up', 'will immediately spin up all disks.')))
            dir.Append(Function(PopupDirectoryItem(ConfirmSpinDown, 'Spin down', 'will immediately spin down all disks.')))
            if CheckInProgress():
                dir.Append(Function(PopupDirectoryItem(CancelParityCheck, 'Parity check in progress', subtitle='Click to cancel',
                    summary=ParityCheckSummary())))
            else:
                dir.Append(Function(PopupDirectoryItem(ConfirmParityCheck, 'Check Parity', subtitle=LastParityCheck(),
                    summary = 'Depending on your system, this may take several hours and may reduce server performance during that time.')))
            dir.Append(Function(PopupDirectoryItem(ConfirmStop, 'Stop Array', 'will take the array off-line.')))
        else:
            dir.Append(Function(PopupDirectoryItem(ConfirmStart, 'Start Array', 'will bring the array on-line.')))
            dir.Append(Function(PopupDirectoryItem(ConfirmReboot, 'Restart', 'will activate a system reset.',
                summary = 'Depending on your system, it may be a few minutes before the server (and the plugin) are back online')))
            dir.Append(Function(PopupDirectoryItem(ConfirmPowerDown, 'Power Down', 'will activate a clean power down.',
                summary = 'Once the server is powered down you will need to power it up manually. There is no "power up" command in this plugin.')))
    else:
        dir.Append(Function(PrefsItem(title='Server Unavailable', subtitle='Cannot connect to unRAID server',
            summary='The server is either offline or not available at the network address specified in the plugin '+
            'preferences. Please confirm that the prefs specify the correct IP address and that the server is online.')))

    dir.Append(PrefsItem(title='Preferences', subtitle='unRAID plugin', thumb=R(PREFS_ICON)))
    
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

def CheckInProgress():
    
    url = Get_unRAID_URL() + '/main.htm'
    mainPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0)
    
    check = mainPage.xpath('//form[@name="mainForm"]/table/tr[2]/td')[0].text
    Log(check)
    
    if check == 'Parity-Check in progress.':
        return True
    else:
        return False

####################################################################################################

def ConfirmParityCheck(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(CheckParity, 'Start Parity check?')))
    return dir

####################################################################################################

def CheckParity(sender):
    
    url = Get_unRAID_URL() + '/update.htm?startState=STARTED&cmdCheck=Check'
    check = HTTP.Request(url).content
    
    return MessageContainer(NAME, L('Parity check has begun.'))

####################################################################################################

def CancelParityCheck(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(CancelCheck, 'Stop current parity check?')))
    return dir

####################################################################################################

def CancelCheck(sender):
    
    url = Get_unRAID_URL() + '/update.htm?startState=STARTED&cmdNoCheck=Cancel'
    cancel = HTTP.Request(url).content
    
    return MessageContainer(NAME, L('Parity check has been cancelled.'))

####################################################################################################

def ParityCheckSummary():
    
    url = Get_unRAID_URL() + '/main.htm'
    mainPage = HTML.StringFromElement(HTML.ElementFromURL(url, errors='ignore', cacheTime=0))
    mainPage = HTML.ElementFromString(mainPage.replace('<strong>','').replace('</strong>',''))
    
    totalSize = mainPage.xpath('//form[@name="mainForm"]/table/tr[3]/td')[1].text
    currentPosition = mainPage.xpath('//form[@name="mainForm"]/table/tr[4]/td')[1].text
    percentComplete = mainPage.xpath('//form[@name="mainForm"]/table/tr[4]/td')[2].text
    estimatedSpeed = mainPage.xpath('//form[@name="mainForm"]/table/tr[5]/td')[1].text
    estimatedFinish = mainPage.xpath('//form[@name="mainForm"]/table/tr[6]/td')[1].text
    syncErrors = mainPage.xpath('//form[@name="mainForm"]/table/tr[7]/td')[1].text
    
    summary = ('Total Size: '+totalSize+'KB\nProgress: '+currentPosition+'KB '+percentComplete+'\n'+
        'Estimated Speed: '+estimatedSpeed+'KB/sec\nEstimated Time to Finish: '+estimatedFinish+' minutes\n'+
        'Sync Errors: '+syncErrors)
    
    return summary

####################################################################################################

def LastParityCheck():
    
    url = Get_unRAID_URL() + '/main.htm'
    mainPage = HTML.StringFromElement(HTML.ElementFromURL(url, errors='ignore', cacheTime=0))
    mainPage = HTML.ElementFromString(mainPage.replace('<strong>','').replace('</strong>','').replace('<br>',''))
    
    #lastCheck = mainPage.xpath('//form[@name="mainForm"]/table/tr[2]/td')[0].text
    lastCheck = mainPage.xpath('//form[@name="mainForm"]/table/tr[2]/td')[2].text
    lastDate = lastCheck.split('on ')[1].split(',')[0]
    lastErrors = lastCheck.split('finding ')[1].split(' errors')[0]
    lastCheck = 'Last: %s Errors: %s' % (lastDate, lastErrors)
    
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