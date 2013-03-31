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
        

from devices import X10Device, InsteonDevice

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
        import datetime

        home = ephem.Observer()
        sun = ephem.Sun() #@UndefinedVariable
        SEC30 = timedelta(seconds=30)
        
        home = ephem.city(self.config['city'])
  
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


    def resolve_time(self, ts, start_time=None):
        from dateutil.parser import parse

        sr, ss = self.sun_times()
       
        ts = ts.strip()
        
        ts = ts.replace('sunset', ss.time().isoformat())
        ts = ts.replace('sunrise', sr.time().isoformat())
        ts = ts.replace('now', datetime.now().time().isoformat())
        
        if '+' in ts or '-' in ts:
            parts = ts.split()
        else:
            parts = [ts]
     
        if parts[0] == '+' or parts [0] == '-':
            if start_time is None:
                raise Exception("Starting with + or - requires specifying a start time")
            if isinstance(start_time, basestring):
                parts = [start_time]+parts
            else:
                parts = [start_time.isoformat()] + parts

     
        time = parse(parts.pop(0))
        
        if len(parts):
            sign = parts.pop(0)
            value = int(parts.pop(0))
        
            td = timedelta(minutes=value)
        
            if sign == '-':
                time = time - td
            else:
                time = time + td
        
        return time

    def commands(self):
        
        commands = []
        last = None
        for e in self.config['schedule']:
            dow = 2
            
            if_ = e.get('if',False)
            if if_ and not eval(if_):
                continue
            
            start =  self.resolve_time(e['from'], start_time=last)
            commands.append({'oo':'on','switch':e['switch'], 
                             'time':start.time().strftime("%H:%M"), 
                             'queue':e.get('queue','default')})
            if e.get('to',False):
                end =  self.resolve_time(e['to'], start_time=start)
                commands.append({'oo':'off','switch':e['switch'], 
                             'time':end.time().strftime("%H:%M"), 
                             'queue':e.get('queue','default')})
            else:
                end = None
                
            last = end
            
        return commands
                
    def del_queues(self):
        import os
        
        queues = set([ c['queue'] for c in self.commands() ])
        
        for queue in queues:
            os.system("at -l -q {} | xargs atrm".format(queue))
        
            
    def schedule(self):
        import os

        self.del_queues()

        for c in self.commands():
            sc = "echo 'insteon_switch --{oo} {switch}' | at -q {queue} {time}".format(**c)
            os.system(sc)
                    