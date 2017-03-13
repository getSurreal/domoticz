# Venstar Thermostat Local API
#
# Author: getSurreal
#
"""
<plugin key="Venstar" name="Venstar Thermostat Local API" author="getSurreal" version="0.1" wikilink="http://www.domoticz.com/wiki/plugins/venstar.html" externallink="http://venstar.com/">
    <params>
        <param field="Address"  label="Address"  width="200px" required="true"  default="192.168.1.x"/>
        <param field="Port"     label="Username" width="200px" required="false" default="80"/>
        <param field="Username" label="Username" width="200px" required="false" default=""/>
        <param field="Password" label="Password" width="200px" required="false" default=""/>
        <param field="Mode6"    label="Debug"    width="75px">
            <options>
                <option label="True"  value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
   </params>
</plugin>
"""
import Domoticz
import urllib
import urllib.parse
import urllib.request
import json
import base64
   
class BasePlugin:
    isConnected = False


    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            Domoticz.Debug("onStart called")
        Domoticz.Transport(Transport="TCP/IP", Address=Parameters["Address"], Port=Parameters["Port"])
        Domoticz.Protocol("HTTP")
        Domoticz.Heartbeat(60)
        Domoticz.Connect()

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Status, Description):
        Domoticz.Debug("onConnect called")
        if (Status == 0):
            self.isConnected = True
            if (1 not in Devices):
                Options = "LevelActions:"+stringToBase64("||||")+";LevelNames:"+stringToBase64("Off|Heat|Cool|Auto")+";LevelOffHidden:ZmFsc2U=;SelectorStyle:MA=="
                Domoticz.Device(Name="Mode",  Unit=1, TypeName="Selector Switch", Switchtype=18, Image=16, Options=Options).Create()
            if (2 not in Devices):
                Options = "LevelActions:"+stringToBase64("||||")+";LevelNames:"+stringToBase64("Auto|On")+";LevelOffHidden:ZmFsc2U=;SelectorStyle:MA=="
                Domoticz.Device(Name="Fan Mode",  Unit=2, TypeName="Selector Switch", Switchtype=18, Image=7, Options=Options).Create()
            if (3 not in Devices): Domoticz.Device(Name="Heat Setpoint", Unit=3, Type=242, Subtype=1).Create()
            if (4 not in Devices): Domoticz.Device(Name="Cool Setpoint", Unit=4, Type=242, Subtype=1).Create()
#            if (5 not in Devices): Domoticz.Device(Name="Dehum Setpoint", Unit=5, Type=244, Subtype=73, Switchtype=7).Create()
            if (6 not in Devices): Domoticz.Device(Name="Temperature", Unit=6, Type=80, Subtype=5).Create()
            if (7 not in Devices): Domoticz.Device(Name="Temp + Humidity", Unit=7, Type=82, Subtype=5).Create()
            if (8 not in Devices): Domoticz.Device(Name="Humidity", Unit=8, Type=81, Subtype=1).Create()
            if (9 not in Devices): Domoticz.Device(Name="Schedule", Unit=9, Type=244, Subtype=73).Create()
            if (10 not in Devices): Domoticz.Device(Name="Away Mode", Unit=10, Type=244, Subtype=73).Create()
        else:
            self.isConnected = False
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"])
            Domoticz.Debug("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+" with error: "+Description)

    def onMessage(self, Data, Status, Extra):
        Domoticz.Debug("onMessage called")
        Data = Data.decode("utf-8", "ignore")
        jsonStr = Data[Data.find('{'):-(len(Data)-Data.rfind('}'))]+'}' # clear everything outside the json curly brackets

        if "success" in jsonStr:
            return
        if "error" in jsonStr:
            Domoticz.Log(jsonStr)
            return

        data = json.loads(jsonStr) # parse json string to dictionary
        UpdateDevice(1,0,str(data['mode']*10))
        UpdateDevice(2,0,str(data['fan']*10))
        if (data['tempunits'] == 0): # If thermostat is in fahrenheit convert to celcius for domoticz
            UpdateDevice(3,0,str((data['heattemp'] -32)*5/9))
            UpdateDevice(4,0,str((data['cooltemp'] -32)*5/9))
            UpdateDevice(6,0,str((data['spacetemp']-32)*5/9))
            UpdateDevice(7,0,str((data['spacetemp']-32)*5/9)+";"+str(data['hum_setpoint'])+";1")
        else:
            UpdateDevice(3,0,str(data['heattemp']))
            UpdateDevice(4,0,str(data['cooltemp']))
            UpdateDevice(6,0,str(data['spacetemp']))
            UpdateDevice(7,0,str(data['spacetemp'])+";"+str(data['hum_setpoint'])+";1")
#            UpdateDevice(5,0,str(data['hum_setpoint']))
        UpdateDevice(8,data['hum_setpoint'],"0")
        UpdateDevice(9,data['schedule'],"0")
        UpdateDevice(10,data['away'],"0")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(int(Level)))
        Domoticz.Debug("mode:"+str(int(Devices[1].sValue))+", fan:"+str(Devices[2].nValue)+", heattemp:"+str(int(float(Devices[3].sValue)*9/5+32))+", cooltemp:"+str(int(float(Devices[4].sValue)*9/5+32)))

        if (Unit == 1): # mode
            mode_val = int(Level/10)
            UpdateDevice(Unit,0,Level)
        else:
            mode_val = int(int(Devices[1].sValue)/10)

        if (Unit == 2): # fan mode
            fan_val = int(Level/10)
            UpdateDevice(Unit,0,Level)
        else:
            fan_val = int(int(Devices[2].sValue)/10)

        if (Unit == 3): # heat temp
            heat_val = int(Level)
        else:
            heat_val = int(float(Devices[3].sValue)*9/5+32)

        if (Unit == 4): # cool temp
            cool_val = int(Level)
        else:
            cool_val = int(float(Devices[4].sValue)*9/5+32)

        if (Unit <= 4):

            params = urllib.parse.urlencode({
                'mode': mode_val,
                'fan': fan_val,
                'heattemp': heat_val,
                'cooltemp': cool_val
            }).encode("utf-8")
            
        if (Unit == 9): # schedule
            if (Command == "On"):
                params = urllib.parse.urlencode({
                    'tempunits': 0,
                    'away': 0,
                    'schedule': 1
                }).encode("utf-8")

            elif (Command == "Off"):
                params = urllib.parse.urlencode({
                    'tempunits': 0,
                    'away': 0,
                    'schedule': 0
                }).encode("utf-8")

        if (Unit == 10): # away
            if (Command == "On"):
                params = urllib.parse.urlencode({
                    'mode': 3,
                    'away': 1,
                    'schedule': 0,
                }).encode("utf-8")

            elif (Command == "Off"):
                params = urllib.parse.urlencode({
                    'mode': 3,
                    'away': 0,
                    'schedule': 1,
                }).encode("utf-8")

#        url = 'http://'+Parameters["Address"]+'/control'
#        response = urllib.request.urlopen(url, params).read()
#        jsonStr = str(response,'utf-8')
#        data = json.loads(jsonStr) # parse json string to dictionary
#        Domoticz.Debug("Venstar Response: "+jsonStr)
        headers = { 'Content-Type': 'application/x-www-form-urlencoded', \
                    'Content-Length' : "%d"%(len(params)) }

        Domoticz.Send(params, "POST", "/control", headers)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self):
        Domoticz.Debug("onDisconnect called")
        self.isConnected = False

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        if (self.isConnected == True):
            url = '/query/info'
            data = ''
            headers = { 'Content-Type': 'text/xml; charset=utf-8', \
                        'Connection': 'keep-alive', \
                        'Accept': 'Content-Type: text/html; charset=UTF-8', \
                        'Host': Parameters["Address"]+":"+Parameters["Port"], \
                        'User-Agent':'Domoticz/1.0', \
                        'Content-Length' : "%d"%(len(data)) }
            Domoticz.Send(data, "GET", url)
#            url = 'http://'+Parameters["Address"]+'/query/info'
#            response = urllib.request.urlopen(url).read()
#            jsonStr = str(response,'utf-8')
#            data = json.loads(jsonStr) # parse json string to dictionary
        else:
            Domoticz.Connect()

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Status, Description):
    global _plugin
    _plugin.onConnect(Status, Description)

def onMessage(Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect():
    global _plugin
    _plugin.onDisconnect()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def stringToBase64(s):
    return base64.b64encode(s.encode('utf-8')).decode("utf-8")

def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
#        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
        Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
        Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return

