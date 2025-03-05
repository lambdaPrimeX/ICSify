import pandas as pd
import base64
import random
import string
from datetime import datetime, timezone
import pathlib as pl
import sys
import logging as log


REPEAT = True
REPEAT_DATE = "20250406T235959Z"
CURRENT_DATETIME = datetime.now()
ics_end_calendar = "END:VCALENDAR" # Define string for calendar ending
ics_events = []


# Configure logging
logger = log.getLogger(__name__)
log.basicConfig(
    filename="icsify.log",
    encoding="utf-8",
    level=log.INFO
)


# Function to fail and escape program
def fail(msg,code):
    logger.info(f"""{msg},{code}""")
    ValueError(msg,code)
    print("Error: %s" % msg)
    sys.exit()

# Function to convert date and time csv into the Google Readable ics format
def convert_from_csv_datetime(date_str, time_str):
    dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%y %H:%M")
    return dt.strftime("%Y%m%dT%H%M%SZ")

# Function to convert date and time ICS into Google Readable format
def convert_to_iso_8601_from_datetime(current_datetime):
    converted_datetime = current_datetime.strftime('%Y%m%dT%H%M%SZ')
    return converted_datetime

# Function to generate a random Base64 UID
def generate_uid():
    random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    return base64.urlsafe_b64encode(random_bytes.encode()).decode().strip("=")

# accepts ICS standard csv i,e titles Subject, Start Date, Start Time, End Date,
# Location, Description,
def convert_csv_to_ics(CSV_FILENAME, EMAIL_ADDRESS, ICS_FILENAME):
    try:
        # Convert csv to DataFrame
        df = pd.read_csv(CSV_FILENAME)
    except ValueError:
        msg = f"""unable to import csv file: {CSV_FILENAME}"""
        logger.info(msg,2)
        return ValueError(msg,2)
    
    ICS_PATH = pl.Path(ICS_FILENAME)
    current_datetime_iso_8601 = convert_to_iso_8601_from_datetime(CURRENT_DATETIME)

    # Define string for calendar beginning
    ics_begin_calendar = "\n".join([
        f"BEGIN:VCALENDAR",
        f"PRODID:-//Google Inc//Google Calendar 70.9054//EN",
        f"VERSION:2.0",
        f"CALSCALE:GREGORIAN",
        f"METHOD:PUBLISH",
        f"X-WR-CALNAME:{EMAIL_ADDRESS}",
        f"X-WR-TIMEZONE:Europe/London]",
        f"BEGIN:VTIMEZONE",
        f"TZID:Europe/London",
        f"X-LIC-LOCATION:Europe/London",
        f"BEGIN:DAYLIGHT",
        f"TZOFFSETFROM:+0000",
        f"TZOFFSETTO:+0100",
        f"TZNAME:GMT+1",
        f"DTSTART:19700329T010000",
        f"RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
        f"END:DAYLIGHT",
        f"BEGIN:STANDARD",
        f"TZOFFSETFROM:+0100",
        f"TZOFFSETTO:+0000",
        f"TZNAME:GMT",
        f"DTSTART:19701025T020000",
        f"RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
        f"END:STANDARD",
        f"END:VTIMEZONE"
        ])

    ics_events.append(ics_begin_calendar)

    for _, row in df.iterrows():
        event_block = ""
        dtstart = convert_from_csv_datetime(row["Start Date"], row["Start Time"])
        dtend = convert_from_csv_datetime(row["End Date"], row["End Time"])
        uid = generate_uid() + "@google.com"
        
        # Populate the event block
        event_block_part_1 = "\n".join([
            f"BEGIN:VEVENT"
        ])
        
        if(REPEAT):
            dt_start_line = f"""DTSTART;TZID=Europe/London:{dtstart[:-1]}"""
            dt_end_line = f"""DTEND;TZID=Europe/London:{dtend[:-1]}"""
            rrule_repeat = f"""RRULE:FREQ=WEEKLY;UNTIL={REPEAT_DATE}"""
            event_block = "\n".join([
                event_block_part_1,
                dt_start_line,
                dt_end_line,
                rrule_repeat,
                ""
            ])
        else:
            event_block = "\n".join([
                event_block_part_1,
                f"DTSTART:{dtstart}",
                f"DTEND:{dtend}",
                ""
            ])

        event_block_part_2 = "\n".join([
            f"""DTSTAMP:{dtend}""",
            f"""UID:{uid}""",
            f"""CREATED:{current_datetime_iso_8601}""",
            f"""LAST-MODIFIED:{current_datetime_iso_8601}""",
            f"""LOCATION:{row["Location"]}""",
            f"SEQUENCE:0",
            f"STATUS:CONFIRMED",
            f"""SUMMARY:{row["Subject"]}""",
            f"TRANSP:OPAQUE",
            f"END:VEVENT"
            ])
        
        event_block = "\n".join([
            event_block + event_block_part_2
        ])
            
        ics_events.append(event_block)

    # Append calender ending to completed calendar
    ics_events.append(ics_end_calendar)

    # Combine all event blocks into one google readable ICS
    ics_file_content = "\n".join(ics_events)

    # Generate placeholder file
    if(ICS_PATH.exists()):
        try:
            ICS_PATH.unlink()
            pl.Path(ICS_PATH).touch()
            with ICS_PATH.open(mode="a", encoding="utf-8") as f:
                f.write(ics_file_content)
        except ValueError:
            fail(f"""Unable to delete existing ics file {ICS_FILENAME}""")
    else:
        pl.Path(ICS_PATH).touch()
        with ICS_PATH.open(mode="a", encoding="utf-8") as f:
            f.write(ics_file_content)


if __name__ == "__main__":
    extension = sys.argv[1][-3:]
    csv_file = sys.argv[1]
    email_address = sys.argv[2]

    if(extension != "csv"):
        fail("invalid filetype. Must be `.csv`",100)

    if len(sys.argv) < 2:
        fail("Missing second argument: CSV filename.",2)

    if len(sys.argv) < 3:
        fail("Missing third argument: email address",3)

    if len(sys.argv) > 4:
        logger.info("Error: too many arguments. Must be `icsify <csv file> <email address> <[output].ics>`.",4)
        raise ValueError(
            "Error: too many arguments given. Must be `icsify <csv file> <email address> <[output].ics>`.",4
        )
    
    if(len(sys.argv) == 3):
        ics_file = "output.ics"
        convert_csv_to_ics(csv_file,email_address,ics_file)

    if(len(sys.argv) == 4):
        ics_file = sys.argv[3]
        convert_csv_to_ics(csv_file,email_address,ics_file)