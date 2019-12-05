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
* DataFrame does adding and splitting for my needs
* DataFrame now contains correct content
* converts to csv in correct format (except bottom)

### needsdoing
* make to integration of csv to to __"official file" automated (+ pdf conv + auto mail)__**
* 450 Border: Magic Const (pay per hour) * Arbeitszeit until now
* shift that are after 00:00