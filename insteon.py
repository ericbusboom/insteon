import httplib
import urllib
import ephem
import time
import yaml
import os
from datetime import datetime, timedelta
from time import localtime, strftime
from dateutil import tz
from time import sleep
        

# Guide for X10 Protocol: http://www.leftovercode.info/smartlinc_x10.html

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
    

class Controller(object):
    
    def __init__(self, config_file):
        
        with open(config_file) as cf:
            self.config = yaml.load(cf)

        self.timezone = tz.gettz(self.config['tz'])
        self.utczone = tz.tzutc()


        if not self.config.get('switches',False):
            raise Exception("Config file dowsn't have 'switches' section")
        
        self.host = self.config['host']
        
    def sun_times(self):


        home = ephem.Observer()
        sun = ephem.Sun()
        SEC30 = timedelta(seconds=30)
        
        home = ephem.city(self.config['city'])
    
        print home
    
        sun.compute(home)
 
        midnight = datetime.datetime.now().replace(hour=0, minute=0,
                                                    second=0, microsecond=0, tzinfo=self.utczone)
        nextrise = (home.next_rising(sun, start=midnight)
        .datetime().replace(tzinfo=self.utczone).astimezone(self.timezone))
        nextset = (home.next_setting(sun, start=midnight)
        .datetime().replace(tzinfo=self.utczone).astimezone(self.timezone))

        return nextrise,nextset

    def resolve(self,name):
        import re
        
        if isinstance(name, basestring):
            if re.match('\w\d+', name):
               g = re.match('(\w)(\d+)', name)
               return  [X10Device(self.host,g.group(1).lower(),g.group(2))]
               
            if re.match('[\w\d]+\.[\w\d]+\.[\w\d]+', name):
                return [InsteonDevice(self.host,name)]
        
        if not isinstance(name, (list, tuple)):
            names = [name]
        else:
            names = name

        out = []
        for name in names:

            value = self.config['switches'].get(name, name)

            if isinstance(value, list):
                out += self.resolve(value)
            elif re.match('\w\d+', value):
                out += self.resolve(value)
            elif re.match('[\w\d]+\.[\w\d]+\.[\w\d]+', value):
                out +=  self.resolve(value)
            else:
                raise Exception('Did not match: {}'.format(value))
        
        return out
    
    def on(self,name):
        switches = self.resolve(name)
        
        for switch in switches:
            switch.on()
        
    def off(self, name):
        switches = self.resolve(name)
        
        for switch in switches:
            switch.off()

import datetime
s = Controller('/etc/insteon.yaml')
#print datetime.datetime.now(),   s.sun_times()

for i in range(0,10):
    s.on(['study', 'livingroom', 'frontlight'])
    time.sleep(1)
    s.off(['study', 'livingroom', 'frontlight'])
    time.sleep(1)
    
    
    
    