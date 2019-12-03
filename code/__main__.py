import os
import datetime
from datetime import date
import calendar

ENTRY_NAMES = ['work', 'Work', 'Bar']  # Names used

workcal_path = os.path.abspath(os.path.join(os.getcwd(), '..'))
rel_path = 'data/workfiles'
workfiles_path = os.path.join(workcal_path, rel_path)
filelist = os.listdir(workfiles_path)  # makes pathes independent of containing superfolder


# todo: search all *.ics files via os

def parse(entry):
    kind, dtime = entry.split('Europe/Berlin:')
    dtime = datetime.datetime.strptime(dtime, '%Y%m%dT%H%M%S')
    kind = 'start' if 'start'.upper() in kind else 'end'
    return kind, dtime


def delta2min(delta):
    return divmod(delta.seconds, 60)[0]


def convert(worktimes):
    worktimes_parsed = [[parse(entry) for entry in day] for day in worktimes if len(day) == 2]
    workrange_shift = [(b[1] if a[0] == 'end' else a[1], a[1] - b[1] if a[0] == 'end' else b[1] - a[1]) for a, b in
                       worktimes_parsed]
    workrange_shift = [(dtime, delta2min(shiftrange)) for dtime, shiftrange in workrange_shift]
    return workrange_shift


def lastmonth():
    tday = date.today()
    end = tday - datetime.timedelta(days=tday.day)
    start = end - datetime.timedelta(days=end.day - 1)
    return start, end


if __name__ == '__main__':

    worktimes_all = []  # stores all for all days the worktimes of a day in list

    for filename in filelist:
        try:
            with open(os.path.join(workfiles_path, filename), 'r') as file:
                content = file.read()
                for possible_entry in ENTRY_NAMES:
                    if possible_entry in content:
                        filelines = content.split('\n')
                        worktimes_all.append([x for x in filelines if 'Europe/Berlin:' in x])
        except UnicodeDecodeError:
            print(f'Error with: {os.path.join(workfiles_path, filename)}')

    startoflastmon, endoflastmon = lastmonth()
    dt_mins = convert(worktimes_all)
    dt_mins.sort()
    workedlastmonth = [dtm for dtm in dt_mins if startoflastmon <= dtm[0].date() <= endoflastmon]
    print(workedlastmonth)
