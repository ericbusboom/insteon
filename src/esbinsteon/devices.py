import httplib
import urllib
import time
import yaml
import os
from datetime import datetime, timedelta
from time import localtime, strftime
from dateutil import tz
from time import sleep

# Guide for X10 Protocol: http://www.leftovercode.info/smartlinc_x10.html

# From reverse-engineering at: http://www.leftovercode.info/smartlinc.html
class InsteonDevice(object):

    command_code_map = {'on':11,'faston':12,'off':13,'fastoff':14,'status':19}

    def __init__(self, host, device):
        import re
        self.host = host
        self.device = device.replace('.','').upper()



    def send(self,command, level=100):
        import time

        api = httplib.HTTPConnection(self.host)

        level = "%0.2X" % int(level / 100 * 255)

        address = ('0262' + 
                    self.device +
                    '0F' +
                    str(self.command_code_map[command]) + 
                    level )+'=I=3'
  
        headers = {}
        
        url = "/3?"+address

        api.request("POST", url, urllib.urlencode({}), headers)
        response = api.getresponse()
        data = response.read()
        return url

    def on(self):
        return self.send('on')

    def off(self):
        return self.send('off')
    
    def __str__(self):
        return str((type(self), self.host, self.device))
    


class X10Device(object):
    
    house_code_map = {'A':'6','B':'E','C':'2','D':'A','E':'1','F':'9','G':'5','H':'D',
                    'I':'7','J':'F','K':'3','L':'B','M':'0','N':'8','O':'4','P':'C'}
    unit_code_map = {1:'600',2:'E00',3:'200',4:'A00',5:'100',6:'900',7:'500',
                    8:'D00',9:'700',10:'F00',11:'300',12:'B00',13:'000',14:'800',15:'400',16:'C00'}

    command_code_map = {'on':280,'off':380,'bright':580,'dim':480,'allon':180,'alloff':680}
    
    def __init__(self, host, house_code, unit_number):
        self.house_code = house_code
        self.unit_number = int(unit_number)
        self.host = host
        
    def _make_command_components(self,command):
        address = ('0263' + 
                    str(self.house_code_map[self.house_code.upper()])+
                    str(self.unit_code_map[self.unit_number]))+'=I=3'

        command = ('0263' +
                    str(self.house_code_map[self.house_code.upper()])+
                    str(self.command_code_map[command]))+'=I=3'

        return (address, command)     
               
    def send(self,command):
        import time

        api = httplib.HTTPConnection(self.host)

        (address, cmd) = self._make_command_components(command)

        headers = {}

        api.request("POST", "/3?"+address, urllib.urlencode({}), headers)
        response = api.getresponse()
        data = response.read()
        
        time.sleep(1)

        api.request("POST", "/3?"+cmd, urllib.urlencode({}), headers)
        response = api.getresponse()

        data = response.read()

    def on(self):
        self.send('on')
    
    def off(self):
        self.send('off')

    def __str__(self):
        return str((type(self), self.host, self.house_code, self.unit_number))
