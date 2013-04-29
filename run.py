#!/usr/bin/python

from twisted.internet import task, reactor

import os
import re
import glob
import time
import urllib
import datetime

from subprocess import call

FILE_PATH   = os.path.abspath(__file__)
CURRENT_DIR = os.path.dirname(FILE_PATH)
OUTPUT_PATH = os.path.join(CURRENT_DIR, "files")

# download interval in seconds
DOWNLOAD_INTERVAL   = 60 * 10
START_TIME          = "08:00"
END_TIME            = "18:00"
SCP_DESTINATION     = False
TIME_SHIFT          = datetime.timedelta(0.5)

def _shifted_datetime():
    return (datetime.datetime.now() + TIME_SHIFT)

def _shifted_date():
    return _shifted_datetime().date()

def _get_image_path():
    return "http://radar.weather.gov/RadarImg/N0R/DOX_N0R_0.gif"

def _str_to_time(timestr):
    (hr, min) = re.match(r'(\d\d):(\d\d)', timestr).groups()
    return datetime.time(int(hr), int(min))

def _date_str():
    return _shifted_datetime().strftime("%Y_%m_%d")

def _ensure_all_directories_exist():
    for dirtype in ["raw", "done"]:
        dirpath = os.path.join(OUTPUT_PATH, dirtype)
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)

def _directory_path(what):
    return os.path.join(OUTPUT_PATH, what, _date_str())

def _ensure_output_directory():
    directory_dest = _directory_path("raw")
    if not os.path.exists(directory_dest):
        os.mkdir(directory_dest)
    return directory_dest

def _is_in_time_range():
    cdt = _shifted_date().timetuple()
    def _dt(t):
        return datetime.datetime(cdt[0], cdt[1], cdt[2], t.hour, t.minute)
    cur_time = _shifted_datetime()
    return (cur_time > _dt(_str_to_time(START_TIME))) and \
            (cur_time < _dt(_str_to_time(END_TIME)))

def retrieve():
    directory_dest = _ensure_output_directory()
    count = len(glob.glob(os.path.join(directory_dest, "*")))
    print "Retrieving %s" % str(count)
    next_name = os.path.join(directory_dest, "%04d.gif" % (count + 1))
    urllib.urlretrieve(_get_image_path(), next_name)

def finalize(path):
    gifs_path = os.path.join(path, "*.gif")
    gifs = sorted(glob.glob(gifs_path))
    outfile = os.path.abspath(os.path.join(path, "..", \
                                "%s.gif" % (_date_str())))
    command = ["gifsicle", "--delay=10", "--loop", "-o", \
                                outfile] + gifs
    call(command)
    return outfile

def tick():
    if _is_in_time_range():
        retrieve()
    else:
        date_raw_path = _directory_path("raw")
        if os.path.exists(date_raw_path):
            print "finalize the images"
            dest = _directory_path("done")
            os.rename(date_raw_path, dest)
            finalized_gif = finalize(dest)
            if SCP_DESTINATION:
                call(["scp", finalized_gif, SCP_DESTINATION])
        else:
            pass

# Twisted code below
def main():
    _ensure_all_directories_exist()
    task.LoopingCall(tick).start(DOWNLOAD_INTERVAL)
    reactor.run()

if __name__ == "__main__":
    main()
