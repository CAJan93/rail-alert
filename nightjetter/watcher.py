import requests
from datetime import date, datetime, timedelta
import os
import argparse
from typing import List


AVAIL_LEVEL_NONE = 0
AVAIL_LEVEL_SEAT = 1
AVAIL_LEVEL_COUCHETTE = 2
AVAIL_LEVEL_PRIVATE_COUCHETTE = 3
AVAIL_LEVEL_BED = 4
AVAIL_LEVEL_PRIVATE_COUCHETTE_OR_BED = 5

prefix = "output"
delimiter = ","

class Nightjetter:
    def __init__(self) -> None:
        self.__session = requests.Session()
        self.__session.headers = {
            "Accept": "application/json",
            "Referer": "https://www.nightjet.com/de/ticket-buchen",
        }
        response = self.__session.post(
            "https://www.nightjet.com/nj-booking/init/start", json={"lang": "de"}
        )
        content = response.json()
        sessionCookie = response.cookies.get("SESSION")
        self.__session.cookies.set("SESSION", sessionCookie)
        self.__session.headers["X-Public-ID"] = content["publicId"]
        self.__session.headers["X-Token"] = content["token"]

        # Get token
        # response = self.__session.post(
        #     "https://www.nightjet.com/nj-booking/init/token",
        #     json={"action": "get", "lang": "de"}
        # )
        # content = response.json()
        # self.__session.headers["CSRF-Token"] = content["CSRF-Token"]

    def findStationId(self, name):
        stations = self.__session.get(
            f"https://www.nightjet.com/nj-booking/stations/find?lang=de&country=at&name={name}"
        )
        stations_json = stations.json()
        # find first non-meta
        target = None
        for station in stations_json:
            if station["name"] != "":
                target = station
                break

        if target is None:
            raise ValueError(f"Station {name} not found!")

        # print(f"Target: {repr(target)}")
        return (target["number"], target["name"])

    def findOffers(self, station_from, station_to, day: datetime.date):
        (station_from_id, _) = self.findStationId(station_from)
        (station_to_id, _) = self.findStationId(station_to)

        fmt_date = "%02d%02d%04d" % (day.day, day.month, day.year)
        connections = self.__session.get(
            f"https://www.nightjet.com/nj-booking/connection/find/{str(station_from_id)}/{str(station_to_id)}/{fmt_date}/00:00?skip=0&limit=1&backward=false&lang=de"
        )
        connections_json = connections.json()
        connections_results = connections_json["results"]
        if len(connections_results) <= 0:
            return None
        first_connection_result = connections_results[0]
        # target_train = first_connection_result["train"]
        departure_time = first_connection_result["from"]["dep_dt"]
        if datetime.fromtimestamp(departure_time / 1000).date() != day:
            return None

        jsonBody = {
            "njFrom": station_from_id,
            "njDep": departure_time,
            "njTo": station_to_id,
            "maxChanges": 0,
            # "filter": {"njTrain": target_train, "njDeparture": departure_time},
            "objects": [
                {
                    "type": "person",
                    "gender": "male",
                    "birthDate": "1993-06-16",
                    "cards": [],  # 100000042 = Klimaticket
                },
                {
                    "type": "person",
                    "gender": "female",
                    "birthDate": "1993-06-16",
                    "cards": [],  # 100000042 = Klimaticket
                },
            ],
            "relations": [],
            "lang": "de",
        }

        response = self.__session.post(
            "https://www.nightjet.com/nj-booking/offer/get", json=jsonBody
        )

        content = response.json()
        if (
            "error" in content
            or content["result"][0] is None
            or len(content["result"][0]["connections"][0]["offers"]) == 0
        ):
            return None
        # print(content)

        first_result = content["result"][0]
        first_connection = first_result["connections"][0]
        return first_connection["offers"]


# Protocol some days
def find_connections(
    station_from: str,
    station_to: str,
    date_start: date,
    advance_days=30,
) -> List[str]:
    jetter = Nightjetter()
    (_, station_from_resl_name) = jetter.findStationId(station_from)
    (_, station_to_resl_name) = jetter.findStationId(station_to)

    all_offers = []
    for i in range(advance_days):
        next_date = date_start + timedelta(days=i)
        print(
            "Processing connection from ",
            station_from_resl_name,
            " to ",
            station_to_resl_name,
            " at",
            str(next_date),
        )
        offers = jetter.findOffers(station_from, station_to, next_date)
        if offers is None:
            continue
        all_offers.append(
            f"found bookable ÖBB Nightjet offer from {station_from} to {station_to} at {str(next_date)}"
        )

    return all_offers
