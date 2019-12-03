# workcal
Apple .ics to csv

### works
* scans dir (one!) of files for specific words (e.g. "work") 
    + so manually search for "work.ics" and copy in folder "data/workfiles"
    + change Magic words 
* gets relevant Datetimeline from file
* parses file and converts to actual Datetime
    + Saves Start of Shift (Datatime)
    + and Amount of minutes for each shift (int)
* gets todays date and calcs last months range (with uneven months, leap etc)
* filters the data, so only last month is included
* creates Pandas DataFrame
* DataFrame does styling for my needs

### needsdoing
* link file with calendar (Execute on every month start)**
* make terminal find, what finder gets manually, at least by brute forcing thru all sub dirs
* make to integration of csv to to __"official file" automated (+ pdf conv + auto mail)__**