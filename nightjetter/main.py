import requests
from datetime import date, datetime,timedelta
import os
import argparse
import io

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
            "Referer": "https://www.nightjet.com/de/ticket-buchen"
        }
        response = self.__session.post(
            "https://www.nightjet.com/nj-booking/init/start",
            json={"lang": "de"}
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
        stations = self.__session.get(f"https://www.nightjet.com/nj-booking/stations/find?lang=de&country=at&name={name}") 
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
        
        fmt_date = "%02d%02d%04d" % (day.day,day.month,day.year)
        connections = self.__session.get(f"https://www.nightjet.com/nj-booking/connection/find/{str(station_from_id)}/{str(station_to_id)}/{fmt_date}/00:00?skip=0&limit=1&backward=false&lang=de")
        connections_json = connections.json()
        connections_results = connections_json["results"]
        if len(connections_results) <= 0:
            return None
        first_connection_result = connections_results[0]
        target_train = first_connection_result["train"]
        departure_time = first_connection_result["from"]["dep_dt"]
        if datetime.fromtimestamp(departure_time / 1000).date() != day:
            return None

        jsonBody = {
            "njFrom": station_from_id,
            "njDep": departure_time,
            "njTo": station_to_id,
            "maxChanges": 0,
            "filter": {
                "njTrain": target_train,
                "njDeparture": departure_time
            },
            "objects": [
                {
                    "type": "person",
                    "gender": "male",
                    "birthDate": "1993-06-16",
                    "cards": [100000042] # 100000042 = Klimaticket
                },
                {
                    "type": "person",
                    "gender": "female",
                    "birthDate": "1993-06-16",
                    "cards": [100000042] # 100000042 = Klimaticket
                }
            ],
            "relations": [],
            "lang": "de"
        }
        
        response = self.__session.post(
            "https://www.nightjet.com/nj-booking/offer/get",
            json=jsonBody
        )

        content = response.json()
        if "error" in content or content["result"][0] is None:
            return None

        first_result = content["result"][0]
        first_connection = first_result["connections"][0]
        return first_connection["offers"]
    
    def findOffersFiltered(self, station_from, station_to, day: datetime.date):
        offers = self.findOffers(station_from, station_to, day)
        if offers is None:
            return None
        
        sparschine = {}
        komfortschiene = {}
        flexschine = {}
        for offer in offers:
            is_spar = False
            is_komfort = False
            if "Kein Storno" in offer["prodGroupLabels"]:
                is_spar = True
            elif "komfortticketStorno" in offer["prodGroupLabels"]:
                is_komfort = True
            elif "Vollstorno" not in offer["prodGroupLabels"]:
                continue
            
            compartments = offer["reservation"]["reservationSegments"][0]["compartments"]
            for compartment in compartments:
                comp_identifier = compartment["externalIdentifier"]
                # print(comp_identifier)
                compartment_object = None
                if "privateVariations" in compartment:
                    compartment_object = compartment["privateVariations"][0]["allocations"][0]["objects"]
                else:
                    compartment_object = compartment["objects"]
                total_price = 0
                for obj_entry in compartment_object:
                    total_price += obj_entry["price"]
                if is_spar:
                    sparschine[comp_identifier] = total_price
                elif is_komfort:
                    komfortschiene[comp_identifier] = total_price
                else:
                    flexschine[comp_identifier] = total_price
        
        # Now calc avail level
        avail_level = AVAIL_LEVEL_NONE
        if "sideCorridorCoach_2" in flexschine or "privateSeat" in flexschine or "centralGangwayCoachComfort_2" in flexschine or "centralGangwayCoachWithTableComfort_2" in flexschine or "serverlyDisabledPerson" in flexschine:
            avail_level = AVAIL_LEVEL_SEAT
        if "couchette4" in flexschine or "couchette6" in flexschine or "couchette4comfort" in flexschine or "femaleCouchette4" in flexschine or "femaleCouchette6" in flexschine or "femaleCouchette4comfort" in flexschine or "couchetteMiniSuite" in flexschine:
            avail_level = AVAIL_LEVEL_COUCHETTE
        if "privateCouchette" in flexschine or "privateCouchette4comfort" in flexschine:
            avail_level = AVAIL_LEVEL_PRIVATE_COUCHETTE
        if "single" in flexschine or "singleWithShowerWC" in flexschine or "double" in flexschine or "doubleWithShowerWC" in flexschine or "singleComfort" in flexschine or "doubleComfort" in flexschine or "singleComfortPlus" in flexschine or "doubleComfortPlus":
            if avail_level == AVAIL_LEVEL_PRIVATE_COUCHETTE:
                avail_level = AVAIL_LEVEL_PRIVATE_COUCHETTE_OR_BED
            else:
                avail_level = AVAIL_LEVEL_BED
        return (avail_level, sparschine, komfortschiene, flexschine)

# Protocol some days
def protocol_connection(jetter: Nightjetter, station_from: str, station_to: str, date_start: date, out_prices: bool, advance_days=30):
    csv_out = f"{prefix}/{station_from}_{station_to}.csv"
    csv_out_price_prefix = f"{prefix}/prices_{station_from}_{station_to}.csv"
    
    (_, station_from_resl_name) = jetter.findStationId(station_from)
    (_, station_to_resl_name) = jetter.findStationId(station_to)

    line_init = ""
    line_time = ""

    results_sparschiene = []
    results_komfortschiene = []
    results_flexschiene = []
    avail_cat_types = set()

    found_offer = False

    for i in range(advance_days):   
        next_date = date_start + timedelta(days=i)
        line_init += str(next_date) + delimiter
        offers = jetter.findOffersFiltered(station_from, station_to, next_date)
        if offers is None:
            line_time += "N" + delimiter
            if csv_out_price_prefix is not None:
                results_sparschiene.append({})
                results_komfortschiene.append({})
                results_flexschiene.append({})
        else:
            found_offer = True
            (avail_level, sparschine, komfortschiene, flexschine) = offers # TODO: protocol prices
            if csv_out_price_prefix is not None:
                results_sparschiene.append(sparschine)
                results_komfortschiene.append(komfortschiene)
                results_flexschiene.append(flexschine)
                for cat_type in sparschine:
                    avail_cat_types.add(cat_type)
                for cat_type in komfortschiene:
                    avail_cat_types.add(cat_type)
                for cat_type in flexschine:
                    avail_cat_types.add(cat_type)
            line_time += str(avail_level) + delimiter
        print("Processing connection from ", station_from_resl_name , " to ", station_to_resl_name ," at", str(next_date))
    
    if not found_offer: 
        print(f"Fail! Did not find any offer for {str(date_start)} + {advance_days} days between {station_from} and {station_to}")
        return
    
    print(f"Success! Found at least one offer for {str(date_start)} + {advance_days} days between {station_from} and {station_to}")
    
    if out_prices:
        print("Outputting prices by category:")
        for cat_type in avail_cat_types:
            fname_sparschiene = csv_out_price_prefix + "-" + cat_type + "-spar.csv"
            fname_komfortschiene = csv_out_price_prefix + "-" + cat_type + "-komf.csv"
            fname_flexschiene = csv_out_price_prefix + "-" + cat_type + "-flex.csv"

            if not os.path.exists(fname_sparschiene):
                with io.open(fname_sparschiene, "w") as csv_out_file:
                    csv_out_file.write(line_init + "\n")
            
            if not os.path.exists(fname_komfortschiene):
                with io.open(fname_komfortschiene, "w") as csv_out_file:
                    csv_out_file.write(line_init + "\n")
            
            if not os.path.exists(fname_flexschiene):
                with io.open(fname_flexschiene, "w") as csv_out_file:
                    csv_out_file.write(line_init + "\n")

            with io.open(fname_sparschiene, "a") as csv_out_file_spar:
                with io.open(fname_komfortschiene, "a") as csv_out_file_komf:
                    with io.open(fname_flexschiene, "a") as csv_out_file_flex:
                        csv_out_file_spar.write(delimiter)
                        csv_out_file_komf.write(delimiter)
                        csv_out_file_flex.write(delimiter)
                        
                        for i in range(advance_days):
                            next_entry_sparschiene = results_sparschiene[i]
                            next_entry_komfortschiene = results_komfortschiene[i]
                            next_entry_flexschiene = results_flexschiene[i]
                            if cat_type in next_entry_sparschiene:
                                csv_out_file_spar.write(str(next_entry_sparschiene[cat_type]) + delimiter)
                            else:
                                csv_out_file_spar.write("N" + delimiter)
                            if cat_type in next_entry_komfortschiene:
                                csv_out_file_komf.write(str(next_entry_komfortschiene[cat_type]) + delimiter)
                            else:
                                csv_out_file_komf.write("N" + delimiter)
                            if cat_type in next_entry_flexschiene:
                                csv_out_file_flex.write(str(next_entry_flexschiene[cat_type]) + delimiter)
                            else:
                                csv_out_file_flex.write("N" + delimiter)
                            
                        
                        csv_out_file_spar.write("\n")
                        csv_out_file_komf.write("\n")
                        csv_out_file_flex.write("\n")

    if not os.path.exists(csv_out):
        with io.open(csv_out, "w") as csv_out_file:
            csv_out_file.write(line_init + "\n")

    with io.open(csv_out, "a") as csv_out_file:
        csv_out_file.write(line_time + "\n")


def test_func(): 
    print("this is a test")

def deprecated():
    jetter = Nightjetter()
    
    # argparse
    parser = argparse.ArgumentParser(description = "find routes at date")
    parser.add_argument("-f", "--from_city", type = str, help = "Departure city.", required=True)
    parser.add_argument("-t", "--to_city", type = str, help = "Destination city.", required=True)
    parser.add_argument("-y", "--year", type = int, help = "year.", required=True)
    parser.add_argument("-m", "--month", type = int, help = "month.", required=True)
    parser.add_argument("-d", "--day", type = int, help = "day.", required=True)
    args = parser.parse_args()

# "Berlin", "Strassburg"
    date_start = date(args.year, args.month, args.day)
    os.makedirs(prefix, exist_ok=True)
    protocol_connection(jetter, args.from_city, args.to_city, date_start, False, 5)
#    protocol_connection(jetter, "Paris", "Berlin", f"{prefix}/hannover_wien.csv", date_start, 180, f"{prefix}/prices_hannover_wien")
    # (wienID, _) = jetter.findStationId("Wien")
    # (hannoverID, _) = jetter.findStationId("Hannover")
    # print(json.dumps(jetter.findOffers("Wien", "Hannover", date(2023, 12, 20)), indent=2))

# TODO: pass  in data and cities 
    


# if there is an offer
# cat output/Berlin_Strassburg.csv  | tail -1 | grep -e [0-9]


