# Venstar Thermostat Local API
#
# Author: getSurreal
#
"""
<plugin key="Venstar" name="Venstar Thermostat Local API" author="getSurreal" version="0.1" wikilink="http://www.domoticz.com/wiki/plugins/venstar.html" externallink="http://venstar.com/">
    <params>
        <param field="Address" label="Address"  width="200px" required="true"  default="127.0.0.1"/>
        <param field="Username"   label="Username" width="200px" required="false" default=""/>
        <param field="Password"   label="Password" width="200px" required="false" default=""/>
        <param field="Mode6"   label="Debug"    width="75px">
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

def stringToBase64(s):
    return base64.b64encode(s.encode('utf-8')).decode("utf-8")
   
class BasePlugin:
    isConnected = False


    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onStart called")
        Domoticz.Transport(Transport="TCP/IP", Address=Parameters["Address"], Port="80")
        Domoticz.Protocol("HTTP")
        Domoticz.Heartbeat(20)
        Domoticz.Connect()
#        return True

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Status, Description):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onConnect called")
        if (Status == 0):
            self.isConnected = True
            if (len(Devices) < 10):
                if (1 not in Devices):
                    Options = "LevelActions:"+stringToBase64("||||")+";LevelNames:"+stringToBase64("Off|Heat|Cool|Auto")+";LevelOffHidden:ZmFsc2U=;SelectorStyle:MA=="
                    Domoticz.Device(Name="Mode",  Unit=1, TypeName="Selector Switch", Switchtype=18, Image=16, Options=Options).Create()
                if (2 not in Devices): #Domoticz.Device(Name="Fan Mode", Unit=2, Type=242).Create()
                    Options = "LevelActions:"+stringToBase64("||||")+";LevelNames:"+stringToBase64("Auto|On")+";LevelOffHidden:ZmFsc2U=;SelectorStyle:MA=="
                    Domoticz.Device(Name="Fan Mode",  Unit=2, TypeName="Selector Switch", Switchtype=18, Image=7, Options=Options).Create()
                if (3 not in Devices): Domoticz.Device(Name="Heat Setpoint", Unit=3, Type=242, Subtype=1).Create()
                if (4 not in Devices): Domoticz.Device(Name="Cool Setpoint", Unit=4, Type=242, Subtype=1).Create()
#                if (5 not in Devices): Domoticz.Device(Name="Dehum Setpoint", Unit=5, Type=244, Subtype=73, Switchtype=7).Create()
                if (6 not in Devices): Domoticz.Device(Name="Temperature", Unit=6, Type=80, Subtype=5).Create()
                if (7 not in Devices): Domoticz.Device(Name="Temp + Humidity", Unit=7, Type=82, Subtype=5).Create()
                if (8 not in Devices): Domoticz.Device(Name="Humidity", Unit=8, Type=81, Subtype=1).Create()
                if (9 not in Devices): Domoticz.Device(Name="Schedule", Unit=9, Type=244, Subtype=73).Create()
                if (10 not in Devices): Domoticz.Device(Name="Away Mode", Unit=10, Type=244, Subtype=73).Create()
                Domoticz.Log("Venstar thermostat devices created.")
                DumpConfigToLog()
        else:
            self.isConnected = False
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"])
            Domoticz.Debug("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+" with error: "+Description)
        return True

    def onMessage(self, Data, Status, Extra):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onMessage called")
        Domoticz.Debug("Data: "+Data)
        Domoticz.Debug("Status: "+Status)
        Domoticz.Debug("Extra: "+Extra)        

    def onCommand(self, Unit, Command, Level, Hue):
        Devices[1].Refresh()
        Devices[2].Refresh()
        Devices[3].Refresh()
        Devices[4].Refresh()

        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(int(Level)))
            Domoticz.Log("mode:"+str(int(Devices[1].sValue))+", fan:"+str(Devices[2].nValue)+", heattemp:"+str(int(float(Devices[3].sValue)*9/5+32))+", cooltemp:"+str(int(float(Devices[4].sValue)*9/5+32)))

        if (Unit == 1):
            mode_val = int(Level/10)
        else:
            mode_val = int(int(Devices[1].sValue)/10)

        if (Unit <= 4):

            if (Unit == 2):
                fan_val = int(Level/10)
            else:
                fan_val = int(int(Devices[2].sValue)/10)

            if (Unit == 3):
                heat_val = int(Level)
            else:
                heat_val = int(float(Devices[3].sValue)*9/5+32)

            if (Unit == 4):
                cool_val = int(Level)
            else:
                cool_val = int(float(Devices[4].sValue)*9/5+32)

            params = urllib.parse.urlencode({
                'mode': mode_val,
                'fan': fan_val,
                'heattemp': heat_val,
                'cooltemp': cool_val
            }).encode("utf-8")
            
        if (Unit == 9):
            if (Command == "On"): val = 1
            elif (Command == "Off"): val = 0
            params = urllib.parse.urlencode({
                'schedule': val,
            }).encode("utf-8")

        if (Unit == 10):
            if (Command == "On"): val = 1
            elif (Command == "Off"): val = 0
            params = urllib.parse.urlencode({
                'away': val,
            }).encode("utf-8")

        url = 'http://'+Parameters["Address"]+'/control'
        response = urllib.request.urlopen(url, params).read()
        jsonStr = str(response,'utf-8')
        data = json.loads(jsonStr) # parse json string to dictionary
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("Venstar Response: "+jsonStr)
            
#        postData = "mode="+int(Devices[1].sValue)+"&fan="+int(Devices[2].sValue)+"&heattemp="+int(float(Devices[3].sValue)*9/5+32)+"&cooltemp="+int(float(Devices[4].sValue)*9/5+32)
#        Domoticz.Send(postData, "POST", "/control", {'Content-Length':str(len(postData))})

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onHeartbeat called")
        if (self.isConnected == True):
#            url = '/query/info'
#            data = ''
#            headers = {"Connection": "keep-alive", "Accept": "Content-Type: text/html; charset=UTF-8"}
#            Domoticz.Send(data, "GET", url)
            url = 'http://'+Parameters["Address"]+'/query/info'
            response = urllib.request.urlopen(url).read()
            jsonStr = str(response,'utf-8')
            data = json.loads(jsonStr) # parse json string to dictionary
            Devices[1].Update(0,str(data['mode']*10))
            Devices[2].Update(0,str(data['fan']*10))
            if (data['tempunits'] == 0): # If thermostat is in fahrenheit convert to celcius for domoticz
                Devices[3].Update(0,str((data['heattemp'] -32)*5/9))
                Devices[4].Update(0,str((data['cooltemp'] -32)*5/9))
                Devices[6].Update(0,str((data['spacetemp']-32)*5/9))
                Devices[7].Update(0,str((data['spacetemp']-32)*5/9)+";"+str(data['hum_setpoint'])+";1")
            else:
                Devices[3].Update(0,str(data['heattemp']))
                Devices[4].Update(0,str(data['cooltemp']))
                Devices[6].Update(0,str(data['spacetemp']))
                Devices[7].Update(0,str(data['spacetemp'])+";"+str(data['hum_setpoint'])+";1")
#            Devices[5].Update(0,str(data['hum_setpoint']))
            Devices[8].Update(data['hum_setpoint'],"0")
            Devices[9].Update(data['schedule'],"0")
            Devices[10].Update(data['away'],"0")
        else:
            Domoticz.Connect()
        return True

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
