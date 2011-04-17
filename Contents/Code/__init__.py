from time import sleep
from WOL import WakeOnLan
from base64 import b64encode

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
    
    #if Prefs['user'] and Prefs['pass']:
    #    HTTP.SetPassword(url=Get_unRAID_URL(), username=Prefs['user'], password=Prefs['pass'])

####################################################################################################

def AuthHeader():
    header = {}

    if Prefs['user'] and Prefs['pass']:
        header = {'Authorization': 'Basic ' + b64encode(Prefs['user'] + ':' + Prefs['pass'])}

    return header

####################################################################################################

def ValidatePrefs():

    #if Prefs['user'] and Prefs['pass']:
    #    HTTP.SetPassword(url=Get_unRAID_URL(), username=Prefs['user'], password=Prefs['pass'])
        
    return

####################################################################################################

def Get_unRAID_URL():
    return 'http://%s' % Prefs['unRAID_host']

####################################################################################################

def ApplicationsMainMenu():

    dir = MediaContainer(viewGroup="InfoList", noCache=True)
    
    startState = GetStartState()
    Log(startState)
    
    
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
        dir.Append(Function(DirectoryItem(UserScriptMenu, 'User Scripts', 'Execute unMenu user scripts')))
    else:
        dir.Append(Function(DirectoryItem(NoAction, title='Server Unavailable', subtitle='Cannot connect to unRAID server',
            summary='The server is either offline or not available at the network address specified in the plugin '+
            'preferences. Please confirm that the prefs specify the correct IP address and that the server is online.')))
        if Prefs['WOL']:
            dir.Append(Function(PopupDirectoryItem(WOLMenu, title='Wake Server', subtitle='Send WOL magic packet to server',
                summary='Attempt to wake a sleeping server by sending a magic packet over the network. Requires the server\'s'+
                ' MAC Address set in the preferences.  Will only work if the server is sleeping and supports Wake-On-LAN.'),
                MACaddress=Prefs['MACaddress']))

    dir.Append(PrefsItem(title='Preferences', subtitle='unRAID plugin', thumb=R(PREFS_ICON)))
    
    return dir

####################################################################################################

def GetDiskStatus():
    
    disks = []
    
    url = Get_unRAID_URL() + '/main.htm'
    mainPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0, headers=AuthHeader())
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
        dir.Append(Function(PopupDirectoryItem(DiskMenu, title=disk['name'], subtitle=disk['s/n'],
            infolabel=disk['temp'], summary='Status: '+disk['status']+'\nSize: '+disk['size']
            +'\nFree Space: '+disk['free']+'\nReads: '+disk['reads']+'\nWrites: '+disk['writes']
            +'\nErrors: '+disk['errors'], thumb=R(DISK_ICON)), diskID=disk['name'], status=disk['status']))
    
    return dir

####################################################################################################

def DiskMenu(sender, diskID, status):
    
    if not Prefs['unMenu']:
        return
    
    dir = MediaContainer(noCache=True)

    url = Get_unRAID_URL() + ':8080/myMain'
    disks = {}
    myMain = HTML.ElementFromURL(url, errors='ignore', cacheTime=0)
    for disk in myMain.xpath('//fieldset//tr'): #/tbody')[0]:
        try:
            diskName = disk.xpath('./td')[1].text
            Log(diskName)
            deviceID = disk.xpath('./td')[2].text
            Log(deviceID)
            if diskName and deviceID:
                disks[diskName] = deviceID
        except:
            continue
        
    Log(disks)
    sequence = myMain.xpath('//fieldset/legend/a')[0].get('href').split('&seq=')[1].split('&')[0]
    Log(sequence)
    if status == 'Spun Up':
        dir.Append(Function(DirectoryItem(SpinDownDisk, title='Spin Down'), diskName=diskID, deviceID=disks[diskID], sequence=sequence))
    elif status == 'Spun Down':
        dir.Append(Function(DirectoryItem(SpinUpDisk, title='Spin Up'), diskName=diskID, deviceID=disks[diskID], sequence=sequence))
    else:
        pass
    return dir

####################################################################################################

def GetStartState():
    
    url = Get_unRAID_URL() + '/main.htm'
    try:
        mainPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0, headers=AuthHeader())
        state = mainPage.xpath('//input[@name="startState"]')[0].get('value')
    except:
        state= 'OFFLINE'
    
    return state

####################################################################################################

def ConfirmStart(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(StartArray, 'Bring array on-line?')))
    return dir

####################################################################################################

def StartArray(sender):

    url = Get_unRAID_URL() + '/update.htm?startState=STOPPED&cmdStart=Start'
    start = HTTP.Request(url, headers=AuthHeader()).content
    
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
    stop = HTTP.Request(url, headers=AuthHeader()).content
    
    return MessageContainer(NAME, L('Array is off-line.'))

####################################################################################################

def ConfirmSpinUp(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(SpinUpArray, 'Spin up all disks?')))
    return dir
    
####################################################################################################

def SpinUpArray(sender):
    
    url = Get_unRAID_URL() + '/update.htm?startState=STARTED&cmdSpinUpAll=Spin+Up'
    spinUp = HTTP.Request(url, headers=AuthHeader()).content
    
    return MessageContainer(NAME, L('Disks in array are spun up.'))

####################################################################################################

def SpinUpDisk(sender, diskName, deviceID, sequence):
    
    url = Get_unRAID_URL() + ':8080/myMain?sort=&view=&seq=%s&dev=%s&disk=%s&cmd=spin&spinind=0' % (sequence, deviceID, diskName)
    response = HTTP.Request(url, headers=AuthHeader()).content
    
    return MessageContainer(NAME, '%s spun up.' % diskName)
    
####################################################################################################

def ConfirmSpinDown(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(SpinDownArray, 'Spin down all disks?')))
    return dir
    
####################################################################################################

def SpinDownArray(sender):
    
    url = Get_unRAID_URL() + '/update.htm?startState=STARTED&cmdSpinDownAll=Spin+Down'
    spinDown = HTTP.Request(url, headers=AuthHeader()).content
    
    return MessageContainer(NAME, L('Disks in array are spun down.'))

####################################################################################################

def SpinDownDisk(sender, diskName, deviceID, sequence):
    
    url = Get_unRAID_URL() + ':8080/myMain?sort=&view=&seq=%s&dev=%s&disk=%s&cmd=spin&spinind=1' % (sequence, deviceID, diskName)
    response = HTTP.Request(url, headers=AuthHeader()).content
    
    return MessageContainer(NAME, '%s spun down.' % diskName)
    
####################################################################################################

def CheckInProgress():
    
    url = Get_unRAID_URL() + '/main.htm'
    mainPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0, headers=AuthHeader())
    
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
    check = HTTP.Request(url, headers=AuthHeader()).content
    
    return MessageContainer(NAME, L('Parity check has begun.'))

####################################################################################################

def CancelParityCheck(sender):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(CancelCheck, 'Stop current parity check?')))
    return dir

####################################################################################################

def CancelCheck(sender):
    
    url = Get_unRAID_URL() + '/update.htm?startState=STARTED&cmdNoCheck=Cancel'
    cancel = HTTP.Request(url, headers=AuthHeader()).content
    
    return MessageContainer(NAME, L('Parity check has been cancelled.'))

####################################################################################################

def ParityCheckSummary():
    
    url = Get_unRAID_URL() + '/main.htm'
    mainPage = HTML.StringFromElement(HTML.ElementFromURL(url, errors='ignore', cacheTime=0, headers=AuthHeader()))
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
    mainPage = HTML.StringFromElement(HTML.ElementFromURL(url, errors='ignore', cacheTime=0, headers=AuthHeader()))
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
    reboot = HTTP.Request(url, headers=AuthHeader()).content
    
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
    powerDown = HTTP.Request(url, headers=AuthHeader()).content
    
    return MessageContainer(NAME, L('The server has been shut down. This plugin will not function until the server has been started again.'))

####################################################################################################

def WOLMenu(sender, MACaddress):
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(SendWOL, 'Send WOL magic packet?'), MACaddress=MACaddress))
    return dir

####################################################################################################

def SendWOL(sender, MACaddress):
    result = WakeOnLan(MACaddress)
    return MessageContainer(NAME, L('Magic packet sent.'))
    
####################################################################################################

def UserScriptMenu(sender):
    
    url = Get_unRAID_URL() + ':8080/user_scripts'
    
    scriptPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0, headers=AuthHeader())
    
    dir = MediaContainer(title2='User Scripts', noCache=True)
    
    for script in scriptPage.xpath('//input[@name="command"]'):
        title = script.get('value')
        dir.Append(Function(DirectoryItem(DoScript, title)))
    
    return dir

####################################################################################################

def DoScript(sender):
    url = Get_unRAID_URL() + ':8080/user_scripts?command=%s' % String.Quote(sender.itemTitle, usePlus=True)
    result = HTTP.Request(url).content
    resultParts = result.split('<hr>')
    scriptOutput = resultParts[-1].split('</BODY>')[0].strip('\n')
    
    return MessageContainer('User Script: "%s" executed' % sender.itemTitle, 'Output: %s' % scriptOutput)
    
####################################################################################################

def NoAction(sender):
    return