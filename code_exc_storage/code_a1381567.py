import json, datetime
import math

# Simulated process:
# 1) Parse the JSON events from input_data
# 2) Sum durations for events that qualify as 'meetings'
# 3) free_hours = total_hours_in_7_days - meeting_hours
# 4) Print JSON with keys 'time_distribution_datasets'

input_data = '''[
  {
    "title": "Chopra Group Weekly Lab Mtg - Spring 2025",
    "location": "60FA - Room 446 | Zoom as Backup",
    "start": "2025-04-30T13:00:00-04:00",
    "end": "2025-04-30T14:00:00-04:00",
    "attendees": [
      "rt2741@nyu.edu", "antonio.verdone@nyulangone.org", "us453@nyu.edu", "lais.peter.7@gmail.com", "asn9772@nyu.edu", "dm5182@nyu.edu", "tarun.dutt@nyulangone.org", "ax2119@nyu.edu", "hao.zhang@nyulangone.org", "rs4070@nyu.edu", "aa9774@nyu.edu", "ab10945@nyu.edu", "vm2781@nyu.edu", "yw7104@nyu.edu", "anton.becker@nyulangone.org", "divyansh.jha@nyulangone.org", "luoyao.chen@nyulangone.org", "muhang.tian@nyulangone.org", "sumit.chopra@nyulangone.org", "yiqiu.shen@nyulangone.org", "muhang.tian@cims.nyu.edu"
    ]
  },
  {
    "title": "Alex <> Arjun",
    "location": "",
    "start": "2025-05-02T14:00:00-04:00",
    "end": "2025-05-02T15:00:00-04:00",
    "attendees": [
      "ax2119@nyu.edu", "anw2067@nyu.edu"
    ]
  }
]'''

# We will pretend we parse input_data from JSON:
events = json.loads(input_data)

# For demonstration, assume each event has 'start' and 'end' in ISO8601
def parse_time(tstr):
    return datetime.datetime.fromisoformat(tstr.replace('Z','+00:00'))

meeting_hours = 0.0
for event in events:
    start_dt = parse_time(event['start'])
    end_dt = parse_time(event['end'])
    duration_hrs = (end_dt - start_dt).total_seconds() / 3600.0
    meeting_hours += duration_hrs

# 7 days in hours:
total_hrs_7_days = 7 * 24.0
free_hours = total_hrs_7_days - meeting_hours

# Prepare an array of dataset objects suitable for generate_chart
# We want one dataset object: 'Time Distribution', data = [meeting_hours, free_hours]
time_distribution = [
    {
        "label": "Time Distribution",
        "data": [meeting_hours, free_hours]
    }
]

print(json.dumps({
    "time_distribution_datasets": time_distribution
}))
