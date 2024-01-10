import requests
import json
from datetime import datetime

class Location:
    def __init__(self, loc_dict):
        self.index = loc_dict.get('index')
        self.id = loc_dict.get('id')
        self.name = loc_dict.get('name')
        self.devices = []

class Device:
    def __init__(self, device_dict):
        self.name = device_dict.get('device_name')
        self.index = device_dict.get('index')
        self.id = device_dict.get('device_id')
        self.sensor_type = device_dict.get('sensor_type_name')
        self.sensor_id = device_dict.get('sensor_id')

def datetime_to_int_seconds(dt_obj):
    epoch_start = datetime(1970, 1, 1)
    return int((dt_obj - epoch_start).total_seconds())

class CrossView:
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.token = None
        self.headers = None
        self.locations = []
        self.__devices = []

        self.login(self.user, self.password)

        if self.token:
            self.headers = {"Authorization": "Bearer " + self.token}
            self.init_locations()

    @property
    def devices(self):
        return self.__devices

    def login(self, email, password):
        url = "https://www.googleapis.com/" \
              "identitytoolkit/v3/relyingparty/verifyPassword?" \
              "key=AIzaSyD-Uo0hkRIeDYJhyyIg-TvAv8HhExARIO4"
        payload = {
            "email": email,
            "returnSecureToken": True,
            "password": password
        }
        r = requests.post(url, data=json.dumps(payload))
        body = r.json()
        self.token = body.get('idToken')

        if self.token is None:
            raise Exception("Login Failed. Check credentials and try again")

    def init_locations(self):
        url = "https://lax-gateway.appspot.com/" \
              "_ah/api/lacrosseClient/v1.1/active-user/locations"
        r = requests.get(url, headers=self.headers)
        if r.status_code < 200 or r.status_code >= 300:
            raise ConnectionError("failed to get locations ()".
                                  format(r.status_code))
        body = r.json()
        n = 0
        for loc in body.get('items'):
            n += 1
            loc['index'] = n
            self.locations.append(Location(loc))
        if not self.locations:
            raise Exception("Unable to get account locations")
        return True

    def get_location_devices(self, location):
        url = "https://lax-gateway.appspot.com/" \
              "_ah/api/lacrosseClient/v1.1/active-user/location/"\
              + location.id\
              + "/sensorAssociations?prettyPrint=false"
        r = requests.get(url, headers=self.headers)
        self.devices.clear()
        body = r.json()
        if body:
            devices = body.get('items')
            n = 0
            for device in devices:
                n += 1
                sensor = device.get('sensor')
                device_name = device.get('name').lower().replace(' ', '_')
                device_dict = {
                    "index": n,
                    "device_name": device_name,
                    "device_id": device.get('id'),
                    "sensor_type_name": sensor.get('type').get('name'),
                    "sensor_id": sensor.get('id'),
                    "sensor_field_names": [x for x in sensor.get('fields')
                                           if x != "NotSupported"],
                    "location": location}
                device_obj = Device(device_dict)
                location.devices.append(device_obj)
                self.devices.append(device_obj)
        return self.devices

    def get_alarm( self, dev_serial ):
        url = "https://ingv2.lacrossetechnology.com/api/v1.1/alarm/" + dev_serial
        r = requests.get(url, headers=self.headers)
        return( r.text )

    def set_alarm( self, dev_serial, payload ):
        url = "https://ingv2.lacrossetechnology.com/api/v1.1/alarm/" + dev_serial
        print("[" + payload + "]")
        r = requests.post( url, headers=self.headers, data=payload )
        return( r.text )

    def get_data_streams( self, dev ):
        url = "https://ingv2.lacrossetechnology.com/api/v1.1/displays/" + dev.sensor_id + "/data-stream"
        r = requests.get(url, headers=self.headers)
        return( r.json() )

    def delete_data_stream( self, dev, stream_id ):
        url = "https://ingv2.lacrossetechnology.com/api/v1.1/displays/" + dev.sensor_id + "/data-stream/" + stream_id
        r = requests.delete(url, headers=self.headers)
        return( r.json() )

    def get_single_stream( self, dev, stream_id ):
        url = "https://ingv2.lacrossetechnology.com/api/v1.1/displays/" + dev.sensor_id + "/data-stream/" + stream_id
        r = requests.get(url, headers=self.headers)
        return( r.json() )

    def add_data_stream( self, dev, message_one, message_two ):
        url = "https://ingv2.lacrossetechnology.com/api/v1.1/displays/" + dev.sensor_id + "/data-stream"
        payload = {"enabled?":True,
                    "featured?":False,
                    "feed":"ref.sensor." + dev.id,
                    "kind":"Elixir.Ingressor.DataStream.Card.MediaCard.V1_1",
                    "message_one":message_one,
                    "message_two":message_two
                   }
        r = requests.post(url, headers={"Authorization": "Bearer " + self.token, "content-type": "application/json"}, data=json.dumps(payload) )
        return( r.json() )

    def update_data_stream( self, dev, stream_id, message_one, message_two ):
        url = "https://ingv2.lacrossetechnology.com/api/v1.1/displays/" + dev.sensor_id + "/data-stream/" + stream_id
        payload = self.get_single_stream( dev, stream_id )
        payload[ "message_one" ] = message_one
        payload[ "message_two" ] = message_two
        r = requests.put(url, headers={"Authorization": "Bearer " + self.token, "content-type": "application/json; charset=UTF-8"}, data=json.dumps(payload) )
        return( r.json() )

    def catalog( self ):
        return [ "air_quality", "chance_damaging_thunderstorms", "chance_hail", "chance_tornado", "grass", "hours_of_sunlight",
                 "mold_risk", "moon_phase", "moonrise_time", "moonset_time", "precipitation_chance", "ragweed", "sky_cover",
                 "snow_accumulation", "sunrise_time", "sunset_time", "tree", "uv_index", "wind_direction", "wind_gust",
                 "wind_speed", "hail_prob_12hr", "sky_cover_12hr", "snow_accumulation_12hr", "thunder_storm_prob_12hr",
                 "tornado_prob_12hr", "wind_dir_12hr", "wind_gust_12hr", "wind_speed_12hr" ]

    def subscribe( self, dev, sub ):
        url = "https://ingv2.lacrossetechnology.com/api/v1.1/displays/" + dev.sensor_id + "/data-stream"
        cat = self.catalog()
        if sub not in cat:
            if sub.isdecimal() and int(sub) >= 1 and int(sub) <= len( cat ):
                sub = cat[ int(sub) - 1 ]
            else:
                return "Not a valid subscription name or number"
        payload =  {"enabled?":True,
                    "feed":"ref.sensor." + dev.id,
                    "kind":"Elixir.Ingressor.DataStream.Card.WeatherReadingCard.V1_1",
                    "reading":sub}
        r = requests.post(url, headers={"Authorization": "Bearer " + self.token, "content-type": "application/json"}, data=json.dumps(payload) )
        return( r.json() )
