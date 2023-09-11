#!/usr/bin/python3
"""
# --------------------------------------------------------------------------
# Low-level python interface for the RTC PCF85063A.
#
# This code does not support all functions of the PCF85063A. This is especially
# relevant for alarms: periodic alarms are not supported at all, i.e. the
# code assumes that alarms are set using specific datetime-values.
#
# Original code from: https://github.com/switchdoclabs/RTC_SDL_DS3231
# forked from:        https://github.com/conradstorz/RTC_SDL_DS3231
# Ported to the PCF85063A.
#
# Author: Bernhard Bablok (methods related to alarms, various changes and fixes)
# License: see below (license statement of the original code)
#
# Website: https://github.com/bablokb/cm4io_rtcctl
#
# --------------------------------------------------------------------------

#encoding: utf-8

# ---------------------- Original header ------------------------------------

# SDL_DS3231.py Python Driver Code
# SwitchDoc Labs 12/19/2014
# V 1.2
# only works in 24 hour mode
# now includes reading and writing the AT24C32 included on the SwitchDoc Labs
#   DS3231 / AT24C32 Module (www.switchdoc.com

# Copyright (C) 2013 @XiErCh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# ---------------------- Original header ------------------------------------
"""

import time
import smbus
from datetime import datetime, timedelta
import arrow                                  # local/utc conversions

# set I2c bus addresses of clock module
PCF85063A_ADDR = 0x51 #known versions of PCF85063A use 0x51

def _bcd_to_int(bcd):
    """
    Decode a 2x4bit BCD to a integer.
    """
    out = 0
    for digit in (bcd >> 4, bcd):
        for value in (1, 2, 4, 8):
            if digit & 1:
                out += value
            digit >>= 1
        out *= 10
    return int(out/10)


def _int_to_bcd(number):
    """
    Encode a one or two digits number to the BCD format.
    """
    bcd = 0
    for idx in (number // 10, number % 10):
        for value in (8, 4, 2, 1):
            if idx >= value:
                bcd += 1
                idx -= value
            bcd <<= 1
    return bcd >> 1


def _set_bit(value,index,state):
    """
    Set bit given by index (zero-based) in value to state and return the result
    """
    mask = 1 << index
    value &= ~mask
    if state:
        value |= mask
    return value

def _local2utc(dtime):
  """
  Convert a naive datetime-object in local-time to UTC
  """
  a = arrow.get(dtime,'local')
  return a.to('utc').naive

def _utc2local(dtime):
  """
  Convert a naive datetime-object in UTC to local-time
  """
  a = arrow.get(dtime,'utc')
  return a.to('local').naive
  
class PCF85063A(object):
    """
    Define the methods needed to read and update the real-time-clock module.
    """

    _SECONDS_REGISTER      = 0x04
    _MINUTES_REGISTER      = 0x05
    _HOURS_REGISTER        = 0x06
    _DAY_OF_WEEK_REGISTER  = 0x08
    _DAY_OF_MONTH_REGISTER = 0x07
    _MONTH_REGISTER        = 0x09
    _YEAR_REGISTER         = 0x0A

    _ALARM_OFFSET         = 0x0B
    _ALARM_SEC_REGISTER   = 0x0B
    _ALARM_MIN_REGISTER   = 0x0C
    _ALARM_HOUR_REGISTER  = 0x0D
    _ALARM_DATE_REGISTER  = 0x0E
    _ALARM_WDAY_REGISTER  = 0x0F

    _CONTROL2_REGISTER      = 0x01

    def __init__(self,port,utc=True,addr=PCF85063A_ADDR):
        """
        constructor
        """
        self._bus = smbus.SMBus(port)
        self._utc = utc
        self._addr = addr

    ###########################
    # PCF85063A real time clock functions
    ###########################
    
    def _write(self, register, data):
        """
        ???
        """
        self._bus.write_byte_data(self._addr, register, data)

    def _read(self, data):
        """
        ???
        """
        return self._bus.read_byte_data(self._addr, data)

    def _read_seconds(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._SECONDS_REGISTER) & 0x7F)   # wipe out the oscillator on bit

    def _read_minutes(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._MINUTES_REGISTER))

    def _read_hours(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._HOURS_REGISTER) & 0x3F)

    def _read_day(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._DAY_OF_WEEK_REGISTER))

    def _read_date(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._DAY_OF_MONTH_REGISTER) & 0x3F)

    def _read_month(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._MONTH_REGISTER) & 0x1F)

    def _read_year(self):
        """
        ???
        """
        return _bcd_to_int(self._read(self._YEAR_REGISTER))

    def read_all(self):
        """
        Return a tuple such as (year, month, daynum, dayname, hours, minutes, seconds).
        """
        return (self._read_year(), self._read_month(), self._read_date(),
                self._read_day(), self._read_hours(), self._read_minutes(),
                self._read_seconds())

    def read_str(self):
        """
        Return a string such as 'YY-DD-MMTHH-MM-SS'.
        """
        return '%02d-%02d-%02dT%02d:%02d:%02d' % (self._read_year(),
                self._read_month(), self._read_date(), self._read_hours(),
                self._read_minutes(), self._read_seconds())

    def read_datetime(self):
        """
        Return the datetime.datetime object.
        """
        dtime =  datetime(2000 + self._read_year(),
                self._read_month(), self._read_date(), self._read_hours(),
                self._read_minutes(), self._read_seconds(), 0)
        if (self._utc):
          return _utc2local(dtime)
        else:
          return dtime

    def write_all(self, seconds=None, minutes=None, hours=None, day_of_week=None,
            day_of_month=None, month=None, year=None):
        """
        Direct write each user specified value.
        Range: seconds [0,59], minutes [0,59], hours [0,23],
                 day_of_week [0,7], day_of_month [1-31], month [1-12], year [0-99].
        """
        if seconds is not None:
            if seconds < 0 or seconds > 59:
                raise ValueError('Seconds is out of range [0,59].')
            seconds_reg = _int_to_bcd(seconds)
            self._write(self._SECONDS_REGISTER, seconds_reg)

        if minutes is not None:
            if minutes < 0 or minutes > 59:
                raise ValueError('Minutes is out of range [0,59].')
            self._write(self._MINUTES_REGISTER, _int_to_bcd(minutes))

        if hours is not None:
            if hours < 0 or hours > 23:
                raise ValueError('Hours is out of range [0,23].')
            self._write(self._HOURS_REGISTER, _int_to_bcd(hours)) # not  | 0x40 according to datasheet

        if year is not None:
            if year < 0 or year > 99:
                raise ValueError('Years is out of range [0, 99].')
            self._write(self._YEAR_REGISTER, _int_to_bcd(year))

        if month is not None:
            if month < 1 or month > 12:
                raise ValueError('Month is out of range [1, 12].')
            self._write(self._MONTH_REGISTER, _int_to_bcd(month))

        if day_of_month is not None:
            if day_of_month < 1 or day_of_month > 31:
                raise ValueError('Day_of_month is out of range [1, 31].')
            self._write(self._DAY_OF_MONTH_REGISTER, _int_to_bcd(day_of_month))

        if day_of_week is not None:
            if day_of_week < 1 or day_of_week > 7:
                raise ValueError('Day_of_week is out of range [1, 7].')
            self._write(self._DAY_OF_WEEK_REGISTER, _int_to_bcd(day_of_week))

    def write_datetime(self, dtime):
        """
        Write from a datetime.datetime object.
        """
        if(self._utc):
            dtime = _local2utc(dtime)

        self.write_all(dtime.second, dtime.minute, dtime.hour,
                dtime.isoweekday(), dtime.day, dtime.month, dtime.year % 100)

    def write_system_datetime_now(self):
        """
        shortcut version of "PCF85063A.write_datetime(datetime.datetime.now())".
        """
        self.write_datetime(datetime.now())

    #######################################################################
    # SDL_PCF85063A alarm handling. Recurring alarms are currently unsupported.
    ########################################################################
    
    def set_alarm_time(self,dtime):
        """
        Set alarm to given time-point. Note: although this method has a
        full datetime-value as input, only the values of day-of-month,
        hours, minutes and seconds (only alarm) are used
        Also disables weekday-alarm bit.
        """
        if (self._utc):
            dtime = _local2utc(dtime)

        self._write(self._ALARM_SEC_REGISTER, _int_to_bcd(dtime.second))
        self._write(self._ALARM_MIN_REGISTER, _int_to_bcd(dtime.minute))
        self._write(self._ALARM_HOUR_REGISTER, _int_to_bcd(dtime.hour))
        self._write(self._ALARM_DATE_REGISTER, _int_to_bcd(dtime.day))
        self._write(self._ALARM_WDAY_REGISTER, 0x80)

    def get_alarm_time(self):
        """
        Query the given alarm and construct a valid datetime-object.
        Return None if no valid alarm has been set.
        """

        # seconds
        buffer = self._read(self._ALARM_SEC_REGISTER)
        if buffer & 0x80:
            return None
        sec = _bcd_to_int(buffer & 0x7F)
        offset = self._ALARM_OFFSET + 1

        # minutes
        buffer = self._read(offset)
        if buffer & 0x80:
            return None
        min  = _bcd_to_int(buffer & 0x7F)

        # hour
        offset = offset + 1
        buffer = self._read(offset)
        if buffer & 0x80:
            return None
        hour = _bcd_to_int(buffer & 0x7F)

        # day-in-month
        offset = offset + 1
        buffer = self._read(offset)
        if buffer & 0x80:
            return None
        day = _bcd_to_int(buffer & 0x3F)

        return self._next_dt_match(day,hour,min,sec)

    def _next_dt_match(self,day,hour,min,sec):
        """
        Calculate the next alarm datetime (in case alarm did not fire yet)
        or the last datetime if the alarm fired.
        The former is exact while the latter is just a best guess - the
        alarm could already have fired way in the past.
        """
        if (self._utc):
            now = datetime.utcnow()
        else:
            now = datetime.now()
        year = now.year
        month = now.month

        enabled,fired = self.get_alarm_state()

        # first try: assume alarm is in the curren month
        # we try to create a valid datetime object
        try:
            alarm_dtime = datetime(year,month,day,hour,min,sec)
        except ValueError:
            # day-of-month might not be valid for current month!
            # no year roll-over necessary, since this won't happen
            # for December or January
            if fired:
                month = month - 1         # alarm must have been in the past
            else:
                month = month + 1         # alarm date is in the future
            alarm_dtime = datetime(year,month,day,hour,min,sec)

        # check if first alarm-datetime is correct
        # this depends on the state of the alarm
        if now > alarm_dtime and not fired:
            # alarm did not fire yet, but must be in the future
            month = month + 1
            if month > 12:
                month = 1
                year  = year + 1
        elif now < alarm_dtime and fired:
            # alarm fired, but must be in the past
            month = month - 1
            if month == 0:
                month = 12
                year = year - 1
        else:
            # proper alignment of now and alarm_dtime, so return it
            if (self._utc):
                return _utc2local(alarm_dtime)
            else:
                return alarm_dtime

        # second try: we moved the alarm one month, but the day-of-month
        # might not be valid for the new month
        try:
            alarm_dtime = datetime(year,month,day,hour,min,sec)
        except ValueError:
            # again, no year roll-over necessary
            if fired:
                month = month - 1      # alarm is in the past, go back in time
            else:
                month = month + 1      # alarm waiting, i.e. in the future
            alarm_dtime = datetime(year,month,day,hour,min,sec)

        if (self._utc):
          return _utc2local(alarm_dtime)
        else:
          return alarm_dtime

    def get_alarm_state(self):
        """
        Query if the state of the alarm. Returns a tuple (enabled,fired)
        of two booleans.
        """
        enabled = self._read(self._CONTROL2_REGISTER) & 0x80  # AIE: bit 7
        fired   = self._read(self._CONTROL2_REGISTER) & 0x40  # AF:  bit 6
        return (bool(enabled),bool(fired))
    
    def clear_alarm(self):
        """
        Clear the given alarm (set AF in the control_2-register to zero)
        """
        control_2 = self._read(self._CONTROL2_REGISTER)
        control_2 &= ~0x40
        self._write(self._CONTROL2_REGISTER,control_2)
        
    def set_alarm(self,state):
        """
        Set the alarm-flag AIE in the control2-register to the
        desired state (0 or 1)
        """
        control_2 = self._read(self._CONTROL2_REGISTER)
        control_2 = _set_bit(control_2,7,state)
        self._write(self._CONTROL2_REGISTER,control_2)

    def dump_value(self,value):
        """
        Dump a value as hex and binary string
        """
        return "0x{0:02X} 0b{0:08b}".format(value,value)
    
    def dump_register(self,reg):
        """
        Read and return a raw register as binary string
        """
        return self.dump_value(self._read(reg))
    
