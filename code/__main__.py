import os
import datetime
from datetime import date
import pandas as pd

ENTRY_NAMES = ['work', 'Work', 'Bar']  # Names used
MAXPERMONTH = 52

workcal_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
rel_path = 'data/workfiles'
workfiles_path = os.path.join(workcal_path, rel_path)
filelist = os.listdir(workfiles_path)  # makes pathes independent of containing superfolder


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

def add_worktime_splitshift(x):
    return f'{x[0] + x[2]}:{(x[1] + x[3]) % 60 if (x[1] + x[3]) % 60 != 0 else "00"}'


def getmonth_ger(monthnum):
    names = ['Januar', 'Februar', 'Maerz', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November',
             'Dezember']
    numtostr = dict((k, v) for k, v in enumerate(names, 1))
    return numtostr[monthnum]


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

    df = pd.DataFrame([list(entry) + 2 * [None] for entry in workedlastmonth],
                      columns=['datetime_shiftstart', 'Arbeitszeit', 'Pausenzeiten von', 'Pausenzeiten bis'])

    df['Arbeitsbeginn'] = [f'{dt.hour}:{dt.minute if dt.minute else "00"}' for dt in df['datetime_shiftstart']]
    df['Tag'] = [dt.date().day for dt in df['datetime_shiftstart']]
    df['Arbeitszeit'] = df['Arbeitszeit'].apply(
        lambda x: f'{x // 60 if x // 60 != 0 else "00"}:{x % 60 if x % 60 != 0 else "00"}')
    df['Arbeitsende'] = df['Arbeitsbeginn'] + ',' + df['Arbeitszeit']
    df['Arbeitsende'] = df['Arbeitsende'].apply(lambda x: [[int(hm) for hm in t.split(':')] for t in x.split(',')])
    df['Arbeitsende'] = df['Arbeitsende'].apply(
        lambda x: f'{x[0][0] + x[1][0]}:{x[0][1] + x[1][1] if x[0][1] + x[1][1] != 0 else "00"}')

    split_shift = list(set([day for day in df['Tag'] if list(df['Tag']).count(day) > 1]))

    drops = []
    for i in range(len(df) - 1):
        if df.loc[i, 'Tag'] == df.loc[i + 1, 'Tag']:
            df.loc[i, 'Pausenzeiten von'] = df.loc[i, 'Arbeitsende']
            df.loc[i, 'Pausenzeiten bis'] = df.loc[i + 1, 'Arbeitsbeginn']
            df.loc[i, 'Arbeitsende'] = df.loc[i + 1, 'Arbeitsende']
            df.loc[i, 'Arbeitszeit'] = add_worktime_splitshift(
                [int(hm) for hm in df.loc[i, 'Arbeitszeit'].split(':')] + [int(hm) for hm in
                                                                           df.loc[i + 1, 'Arbeitszeit'].split(':')])
            drops.append(i + 1)
    for row in drops:
        df = df.drop(row)

    df = df.drop('datetime_shiftstart', axis=1)
    df['Entlohnungsart'] = len(df) * [None]

    c = df.columns.tolist()
    c[0], c[1], c[2], c[3], c[4], c[5], c[6] = c[3], c[5], c[1], c[2], c[0], c[6], c[4]
    df = df[c]
    df.index += 1

    blank = [None] * 6
    real = pd.DataFrame([blank] * 31,
                        columns=['Arbeitsbeginn', 'Arbeitsende', 'Pausenzeiten von', 'Pausenzeiten bis', 'Arbeitszeit',
                                 'Entlohnungsart'])
    real.index += 1

    # entire month join
    # todo: join to Year work list
    for i in range(1, 32):
        isday = df[df['Tag'] == i]
        isday = isday.drop('Tag', axis=1)
        if not isday.empty:
            real.loc[i, :] = isday.iloc[0]
    real.index.name = 'Tag'

    filename = str(startoflastmon)[:-3].split('-')
    savepath = f'Stunden_Nils_Seitz_{ filename[0]}{filename[1]}_{getmonth_ger(int(filename[1]))}.csv'
    real.to_csv(os.path.join('/Users/nilsseitz/Desktop', savepath))

    # todo: make border of 52h
    for i in range(1, 32):
        isday = df[df['Tag'] == i]
        isday = isday.drop('Tag', axis=1)
        if not isday.empty:
            real.loc[i, :] = isday.iloc[0]
    real.index.name = 'Tag'

    filename = str(startoflastmon)[:-3].split('-')
    savepath = f'Stunden_Nils_Seitz_{filename[0]}{filename[1]}_{getmonth_ger(int(filename[1]))}_official.csv'
    real.to_csv(os.path.join('/Users/nilsseitz/Desktop', savepath))