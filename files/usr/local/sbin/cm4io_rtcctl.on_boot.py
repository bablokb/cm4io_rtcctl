#!/usr/bin/python3
# --------------------------------------------------------------------------
# Helper-Script for boot-processing.
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/cm4io_rtcctl
# --------------------------------------------------------------------------

import time, subprocess, datetime

import pcf85063a

# --- settings   -----------------------------------------------------------

utc=True                    # all times in the RTC are stored as utc
                            # with automatic conversion while reading
MAX_WAIT = 30               # maximum wait time for time synchronization

# --- check state of RTC   -------------------------------------------------

def _check_rtc(ts):
  """ check if RTC has a valid time """

  return (ts.year > 2025 and ts.year < 2099 and
          ts.month > 0 and ts.month < 13 and
          ts.day > 0 and ts.day < 32 and
          ts.hour < 25 and ts.minute < 60 and ts.second < 60)

# --- manual boot processing   ---------------------------------------------

def handle_manual_boot():
  """ handle manual boot """

  # get rtc time and check if it is valid
  ts = rtc.read_datetime()
  if not _check_rtc(ts):
    print("rtc time is not valid, updating from system time")
    # update rtc time from system time
    rtc.write_system_datetime_now()
  else:
    # update system time from rtc
    print("updating system time from rtc")
    subprocess.run(['date', '-s', f'{rtc.read_datetime()}'])

# --- main program   -------------------------------------------------------

if __name__ == "__main__":
  rtc = pcf85063a.PCF85063A(10,utc)               # use i2c-10
  (enabled,fired) = rtc.get_alarm_state()
  print(f"rtc alarm state: {enabled=}, {fired=}")
  if not fired:
    handle_manual_boot()
  else:
    # assume valid rtc, update system time from rtc
    subprocess.run(['date', '-s', f'{rtc.read_datetime()}'])
    
  # turn off alarm
  rtc.clear_alarm()
  rtc.set_alarm(0)
