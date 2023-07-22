import pandas
import requests
import datetime
from bs4 import BeautifulSoup, NavigableString

class Day:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class Stage:
    def __init__(self, stage_name):
        self.name = stage_name

class Artist:
    def __init__(self, name):
        self.name = name

class Timeslot:
    def __init__(self, start, end):
        self.start = start[11:19]
        self.end = end[11:19]

class Performance:
    def __init__(self, artist, stage, timeslot, day):
        self.artist = artist
        self.stage = stage
        self.timeslot = timeslot
        self.day = day

    def to_dict(self):
        return {
            "artist_name": self.artist.name,
            "stage_name": self.stage.name,
            "day_id": self.day.id,
            "day_name": self.day.name,
            "timeslot_start": self.timeslot.start,
            "timeslot_end": self.timeslot.end,
        }

def addOrGetArtist(artistname, artists):
    for artist in artists:
        if artist.name == artistname:
            return artist

    artist = Artist(artistname)
    artists.append(artist)
    return artist
        

page = requests.get('https://www.tomorrowland.com/en/festival/line-up')
soup = BeautifulSoup(page.content, "html.parser")

valid_event_day_ids = [135, 136, 137, 138]

event_days_container = soup.find(class_="eventdays")
event_days = event_days_container.find_all(class_="eventday")

all_artists = []
all_performances = []

for event_day in event_days:
    event_day_text = event_day['data-eventday']
    event_day_id = event_day['data-eventday-id']
    day = Day(event_day_id, event_day_text)

    is_valid_day = False;

    for valid_day in valid_event_day_ids:
        if int(event_day_id) == valid_day:
            is_valid_day = True

    if is_valid_day:
        stages = event_day.find_all(class_="stage")
        stage_headings = []
        for stage in stages:
            inner_text = [element for element in stage.h4 if isinstance(element, NavigableString)]
            stage_headings.append(inner_text[0].strip())
        
        performances = event_day.find(class_="performances")
        container = performances.find(class_="stage__performances-container")
        stage_performances = container.find_all(class_="stage__performances")
        stage_index = 0;
        for stage_performance in stage_performances:
            stage_name = stage_headings[stage_index]
            current_stage = Stage(stage_name)
            all_stage_performances = stage_performance.find_all(class_="performance")
            for performance in all_stage_performances:
                performance_start = performance['data-start']
                performance_end = performance['data-end']

                performance_inner = performance.find(class_="performance__inner__overlay")
                performance_info = performance_inner.find(class_="performance__info")

                new_info_text = []
                for info in performance_info:
                    info_text = info.text.strip().split('\n')
                    for extracted_text in [i for i in info_text if i]:
                        new_info_text.append(extracted_text)

                
                performance_artist_text = new_info_text[0]
                performance_artist_time = new_info_text[1]

                artist = addOrGetArtist(performance_artist_text, all_artists)
                timeslot = Timeslot(performance_start, performance_end)
                performance = Performance(artist, current_stage, timeslot, day)
                all_performances.append(performance)

            stage_index = stage_index + 1


df = pandas.DataFrame.from_records([performance.to_dict() for performance in all_performances])

df.to_csv("csv/timetables.csv")
