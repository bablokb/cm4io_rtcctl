#!/usr/bin/python3
# --------------------------------------------------------------------------
# Control script for PCF85063A-RTC
#
# Note that times in the RTC are stored in UTC. You can change this
# behavior by changing the utc-variable to False.
#
# Supported commands
#  help  - dump list of available commands
#  init  - initialize registers with sensible values
#  show  - display datetime, alarm, sys or all
#  dump  - display registers (binary format)
#  set   - datetime, alarm, sys times
#  on    - turn alarm on
#  off   - turn alarm on
#  clear - clear alarm-flag
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/cm4io_rtcctl
#
# --------------------------------------------------------------------------

import os, sys, re, datetime

import pcf85063a

# --- settings   -----------------------------------------------------------

utc=True                    # all times in the RTC are stored as utc
                            # with automatic conversion while reading

# --- help   ---------------------------------------------------------------

def help():
  """
  Dump list of available commands
  """
  print( """
Available commands (date and time are synonyms):
     help                                - dump list of available commands
     init                                - initialize RTC
     show  [date|time|alarm|sys]         - display given type or all
     dump  [control|date|time|alarm]     - display registers (hex/binary format)
     set   date|time|alarm|sys           - set rtc-date, alarm, sys-date
                                           Format: dd.mm.YYYY [HH:MM[:SS]] or
                                                   mm/dd/YYYY [HH:MM[:SS]]
                                           (does not turn alarm on!)
     alarm on                            - turn alarm on
     alarm off                           - turn alarm off
     alarm clear                         - clear alarm-flag
  """)

# --- init   ---------------------------------------------------------------

def init(rtc,argv=[]):
  """
  Initialize RTC (set rtc-datetime to system-datetime, set alarm-times
  and clear/disable alarms)
  """
  rtc.write_system_datetime_now()
  rtc.set_alarm_time(datetime.datetime.now())
  rtc.clear_alarm()
  rtc.set_alarm(0)

# --- show   ---------------------------------------------------------------

def show(rtc,argv=[]):
  """
  Display date, time, alarm or all (date and time are synonyms)
  
  Arg: date|time|alarm|sys|all (default: all)
  """
  if len(argv) == 0:
    show(rtc,["date"])
    show(rtc,["sys"])
    show(rtc,["alarm"])
  elif argv[0] == "date" or argv[0] == "time":
    print("date:   %s" % rtc.read_datetime())
  elif argv[0] == "alarm":
    print("alarm:  %s" % rtc.get_alarm_time())
    (enabled,fired) = rtc.get_alarm_state()
    print("        (enabled: %s)" % enabled)
    print("        (fired:   %s)" % fired)
  elif argv[0] == "sys":
    print("sys:    %s" % datetime.datetime.now())
  else:
    print("invalid argument")

# --- dump   ---------------------------------------------------------------

def dump(rtc,argv=[]):
  """
  Display registers (hex/binary format)

  Arg: control|date|time|alarm|all (default: all)
  """
  if len(argv) == 0:
    dump(rtc,["control"])
    dump(rtc,["date"])
    dump(rtc,["alarm"])
  elif argv[0] == "control":
    print("control:        %s" % rtc.dump_register(rtc._CONTROL2_REGISTER))
  elif argv[0] == "date" or argv[0] == "time":
    print("date  (sec):   %s" % rtc.dump_register(rtc._SECONDS_REGISTER))
    print("date  (min):   %s" % rtc.dump_register(rtc._MINUTES_REGISTER))
    print("date  (hour):  %s" % rtc.dump_register(rtc._HOURS_REGISTER))
    print("date  (weekd): %s" % rtc.dump_register(rtc._DAY_OF_WEEK_REGISTER))
    print("date  (day):   %s" % rtc.dump_register(rtc._DAY_OF_MONTH_REGISTER))
    print("date  (month): %s" % rtc.dump_register(rtc._MONTH_REGISTER))
    print("date  (year):  %s" % rtc.dump_register(rtc._YEAR_REGISTER))
  elif argv[0] == "alarm":
    print("alarm (sec):   %s" % rtc.dump_register(rtc._ALARM_SEC_REGISTER))
    print("alarm (min):   %s" % rtc.dump_register(rtc._ALARM_MIN_REGISTER))
    print("alarm (hour):  %s" % rtc.dump_register(rtc._ALARM_HOUR_REGISTER))
    print("alarm (date):  %s" % rtc.dump_register(rtc._ALARM_DATE_REGISTER))
  else:
    print("invalid argument")

# --- set   ----------------------------------------------------------------

def set(rtc,argv):
  """
  set date, time, alarm (date and time are synonyms)
  
  Arg: date|time|alarm
  """
  if argv[0] == "date" or argv[0] == "time":
    if len(argv) == 1:
      rtc.write_system_datetime_now()
      return
  elif argv[0] == "sys":
    dtime = rtc.read_datetime()
    os.system('date -s "%s"' % dtime)
    return

  dateString = argv[1] + (" " + argv[2] if len(argv) > 2 else "")
  if '/' in dateString:
    format = "%m/%d/%Y %H:%M:%S"
  else:
    format = "%d.%m.%Y %H:%M:%S"

  # add default hour:minutes:secs if not provided
  if ':'  not in dateString:
    dateString = dateString + " 00:00:00"

  # parse string and check if we have six items
  dateParts= re.split('\.|/|:| ',dateString)
  count = len(dateParts)
  if count < 5 or count > 6:
    print("illegal datetime format!")
    print("Must be mm/dd/yy[yy] [HH:MM[:SS]] or")
    print("        dd.mm.yy[yy] [HH:MM[:SS]]")
    return
  elif count == 5:
    dateString = dateString + ":00"

  if len(dateParts[2]) == 2:
    format = format.replace('Y','y')

  if argv[0] == "alarm":
    rtc.set_alarm_time(datetime.datetime.strptime(dateString,format))
  elif argv[0] == "date" or argv[0] == "time":
    rtc.write_datetime(datetime.datetime.strptime(dateString,format))
  else:
    print("invalid argument")

# --- alarm on/off/clear   -------------------------------------------------

def alarm(rtc,argv):
  """
  change alarm state
  """
  if argv[0] == "on":
    rtc.set_alarm(1)
  elif argv[0] == "off":
    rtc.set_alarm(0)
  elif argv[0] == "clear":
    rtc.clear_alarm()
  else:
    print("invalid argument")

# --- main program   ------------------------------------------------------

if __name__ == "__main__":
  if len(sys.argv) == 1:
    help()
  else:
    funcs = locals()
    command = sys.argv[1]
    if command == 'help':
      help()
    elif command in funcs:
      rtc = pcf85063a.PCF85063A(10,utc)               # use i2c-10
      funcs[command](rtc,sys.argv[2:])
    else:
      print("command %s not found!" % command)
      help()
