#!usr/local/bin/python3
import os
import sys

import numpy as np
import pandas as pd
import itertools
import datetime
from datetime import date

OFFICIAL_MAX: int = 48
tday: datetime.date = date.today()
endoflastmon: pd.Timestamp = pd.Timestamp(
    tday - datetime.timedelta(days=tday.day))
startoflastmon: pd.Timestamp = pd.Timestamp(
    endoflastmon - datetime.timedelta(days=endoflastmon.day - 1))
endoflastmon = pd.Timestamp(tday - datetime.timedelta(days=tday.day - 1))
path: str = '/Users/nilsseitz/Desktop/work.txt'

# OVERWRITE AND EXECUTE MANUALLY (NOT IN AUTOMATOR SCRIPT) FOR OTHER MONTHS
# year = 2020
# month = 6
# startoflastmon = pd.Timestamp(date(year, month, 1))
# endoflastmon = pd.Timestamp(date(year, month + 1, 1))


def delta2min(delta):
    return divmod(delta.seconds, 60)[0]


def add_worktime_splitshift(x):
    return f'{(x[0] + x[2]) % 24}:{(x[1] + x[3]) % 60 if (x[1] + x[3]) % 60 != 0 else "00"}'


def getmonth_ger(monthnum):
    names = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November',
             'Dezember']
    numtostr = dict((k, v) for k, v in enumerate(names, 1))
    return numtostr[monthnum]


def make_dataframe(single_shifts):
    workedlastmonth = pd.DataFrame(single_shifts, columns=[
                                   'Date (Start)', 'Date (End)', 'Time (Start)', 'Time (End)'])
    workedlastmonth['datetime_shiftstart'] = (workedlastmonth['Date (Start)'] + workedlastmonth['Time (Start)']) \
        .apply(lambda x: datetime.datetime.strptime(x, '%d.%m.%y%H:%M:%S'))
    workedlastmonth['amount_min'] = (workedlastmonth['Time (End)'].
                                     apply(lambda x: datetime.datetime.strptime(
                                         x, '%H:%M:%S'))
                                     - workedlastmonth['Time (Start)'].
                                     apply(lambda x: datetime.datetime.strptime(x, '%H:%M:%S'))). \
        apply(lambda x: delta2min(x))
    workedlastmonth = workedlastmonth[startoflastmon <=
                                      workedlastmonth['datetime_shiftstart']]
    workedlastmonth = workedlastmonth[workedlastmonth['datetime_shiftstart'] <= endoflastmon]
    workedlastmonth = workedlastmonth.drop(
        ['Date (Start)', 'Date (End)', 'Time (Start)', 'Time (End)'], axis=1)
    workedlastmonth = workedlastmonth.reset_index(drop=True)
    worktime_frac_hours = workedlastmonth['amount_min'].sum() / 60

    return workedlastmonth.fillna(0), int(worktime_frac_hours) if worktime_frac_hours.is_integer() else worktime_frac_hours


def make_official_df(workedlastmonth):
    official_split = OFFICIAL_MAX * 60
    sum_of_workinghours = workedlastmonth['amount_min'].sum()
    if official_split > sum_of_workinghours:  # Error otherwise!
        worktime_in_hours = sum_of_workinghours / 60
        return workedlastmonth.fillna(0), int(worktime_in_hours) if worktime_in_hours.is_integer() else worktime_in_hours
    else:
        workedlastmonth_official = workedlastmonth[workedlastmonth['amount_min'].cumsum(
        ) < official_split]
        rest = official_split - workedlastmonth_official['amount_min'].sum()
        workedlastmonth_official = workedlastmonth_official.append(
            workedlastmonth.loc[len(workedlastmonth_official)])
        workedlastmonth_official.loc[len(
            workedlastmonth_official) - 1, 'amount_min'] = rest
        return workedlastmonth_official.fillna(0), OFFICIAL_MAX


def format_dataframe(df):
    df = df.append(pd.DataFrame(np.full((0, 4), 0), columns=['Arbeitsbeginn', 'Tag', 'Arbeitszeit',
                                                             'Arbeitsende']))
    df['Arbeitsbeginn'] = [
        f'{dt.hour}:{dt.minute if dt.minute != 0 else "00"}' for dt in df['datetime_shiftstart']]
    df['Tag'] = [dt.date().day for dt in df['datetime_shiftstart']]
    df['Arbeitszeit'] = df['amount_min'].apply(
        lambda x: f'{int(x) // 60 if int(x) // 60 != 0 else "00"}:{int(x) % 60 if int(x) % 60 != 0 else "00"}')
    df['Arbeitsende'] = df['Arbeitsbeginn'] + ',' + df['Arbeitszeit']
    df['Arbeitsende'] = df['Arbeitsende'].apply(
        lambda x: [[int(hm) for hm in t.split(':')] for t in x.split(',')])
    df['Arbeitsende'] = df['Arbeitsende'].apply(
        lambda x: f'{(x[0][0] + x[1][0]) % 24}:{(x[0][1] + x[1][1]) % 60 if (x[0][1] + x[1][1]) % 60 != 0 else "00"}')

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

    df = df.drop(['datetime_shiftstart', 'amount_min'], axis=1)

    c = df.columns.tolist()
    #   ['Arbeitsbeginn', 'Arbeitsende', 'Arbeitszeit', 'Tag' ]
    # ->  Tag, Arbeitsbeginn, Arbeitsende, von , bis, Arbeitszeit

    c[0], c[1], c[2], c[3] = c[3], c[0], c[1], c[2]
    df = df[c]
    df.index += 1

    blank = [None] * 6
    formatted = pd.DataFrame([blank] * 31,
                             columns=['Arbeitsbeginn', 'Arbeitsende', 'Pausenzeiten von', 'Pausenzeiten bis',
                                      'Arbeitszeit', 'Entlohnungsart'])
    formatted.index += 1

    for i in range(1, 32):
        isday = df[df['Tag'] == i]
        isday = isday.drop('Tag', axis=1)
        if not isday.empty:
            formatted.loc[i, :] = isday.iloc[0]

    formatted.index.name = 'Tag'
    formatted.replace(to_replace=[None], value=np.nan, inplace=True)
    return formatted


def add_monthly_sum(df, sum):
    df.loc['Summe', 'Arbeitszeit'] = sum
    return df


if __name__ == '__main__':

    single_shifts = []
    with open(path, 'r') as f:
        shifts = list(f)[3:-1]  # clean file of header and last empty line

        shift = []
        # split and clean single shifts, so only Date&Time are left (per shift)
        for line in shifts:
            if line == '\n':
                single_shifts.append(shift)
                shift = []
            elif line.startswith('Date'):
                # cleaning unnecessary pre- and suffix
                shift.append(line.strip('Date:\t')[:-1].split(' to '))
            elif line.startswith('Time'):
                shift.append(line.strip('Time:\t')[:-1].split(' to '))
            else:
                pass

    single_shifts = [list(itertools.chain.from_iterable(shift))
                     for shift in single_shifts]

    df, month_sum = make_dataframe(single_shifts)
    df_official, month_sum_official = make_official_df(df)

    filename = str(startoflastmon)[:-3].split('-')
    savepath = f'Stunden_Nils_Seitz_{filename[0]}{filename[1]}_{getmonth_ger(int(filename[1]))}'

    df_formatted = format_dataframe(df)
    df_formatted = add_monthly_sum(df_formatted, month_sum)
    overtime = month_sum - OFFICIAL_MAX
    overtime_str = ''
    if overtime > 0:
        overtime_str = f'{overtime} Überstunden'
    elif overtime < 0:
        overtime_str = f'{-overtime} Minusstunden'

    with open('/Users/nilsseitz/Documents/Arbeit/Waldperle/Stunden2020/realworkhours/overtime.txt', 'r+') as f:
        readin = f.read()
        recent_overtime_str, recent_month = readin.split(',')
        recent_overtime = float(recent_overtime_str)
        recent_overtime += overtime

    with open('/Users/nilsseitz/Documents/Arbeit/Waldperle/Stunden2020/realworkhours/overtime.txt', 'w') as f:
        new_recent_month = getmonth_ger(tday.month)
        if new_recent_month != recent_month:
            f.write(f'{recent_overtime},{new_recent_month}')
        else:
            f.write(readin)

    df_formatted.loc['Summe', 'Entlohnungsart'] = overtime_str
    df_formatted.to_csv(os.path.join(
        '/Users/nilsseitz/Desktop', f'{savepath}.csv'))

    df_official_formatted = format_dataframe(df_official)
    df_official_formatted = add_monthly_sum(
        df_official_formatted, month_sum_official)
    df_official_formatted.to_csv(os.path.join(
        '/Users/nilsseitz/Desktop', f'{savepath}_official.csv'))

    sys.exit()
