Introduction
============

This project implements a control script for the RTC of the Raspberry Pi CM4IO
and similar boards that use the same design, e.g. Cytron's CM4 Maker Board
or Waveshare's CM4-boards.

The script runs in userspace. It will only work if the kernel is not in
control of the RTC, i.e. there is no overlay configured for the PCF85063A.


Software
--------

The software consists of a program to control the RTC and a system daemon
which takes care of

  - setting the system-time after boot (optional)
  - clearing alarms after boot
  - setting the alarm (next boot time) at shutdown (optional)


Installation
============

Clone the archive and then run the install-command from the tools-directory:

    git clone https://github.com/bablokb/cm4io_rtcctl.git
    cd cm4io_rtcctl
    sudo tools/install

Besides changing some system configuration files, this command will
mainly install three components (and there prereqs):

  - `cm4io_rtcctl.py`, the control program for the real-time-clock
  - `cm4io_rtcctl.service`, the systemd-service

After installation, you should reboot your system to activate the changes.


Initializing the real-time-clock
--------------------------------

If your real-time-clock is not yet set, you have to initialize it once.
Make sure that you have an internet connection so the ntp-daemon updates
the system time. Check the system time and the time of the RTC:

    date
    sudo cm4io_rtcctl.py show date

If the system time is correct and the time matches, you are done. Otherwise
initialize the RTC once with:

    sudo cm4io_rtcctl.py init

Note that the standard linux tool `hwclock` will not work, since we don't
expose the standard RTC-device interface of the RTC.

For the cm4io-board, a coincell backup-battery is not strictly required
as long as the board is powered. Cytron's "CM4 Maker Board" in contrast
turns power off after shutdown. This is far more efficient but it
makes the coincell mandatory.


Usage
=====

The command `/usr/local/sbin/cm4io_rtcctl.py` is the main user-interface to the
real time clock. With this command, you can read and write the RTC-time,
set the alarm time, turn the alarm on, off or clear an alarm that has
fired:

    [root@cm4:~] # cm4io_rtcctl.py help

    Available commands (date and time are synonyms):
         help                                - dump list of available commands
         init                                - initialize RTC
         show  [date|time|alarm|sys]         - display given type or all
         dump  [control|date|time|alarm]     - display registers (hex/binary format)
         set   date|time|alarm|sys           - set RTC-date, alarm, sys-date
                                               Format: dd.mm.YYYY [HH:MM[:SS]] or
                                                       mm/dd/YYYY [HH:MM[:SS]]
                                               (does not turn alarm on!)
         alarm on                            - turn alarm on
         alarm off                           - turn alarm off
         alarm clear                         - clear alarm-flag
