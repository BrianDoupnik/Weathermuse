import sys
import secrets
import json
import requests
import ipinfo
from datetime import datetime

#declare global variables
arguments = sys.argv
spotify_id = secrets.spotify_user_id
spotify_token = secrets.spotify_token
ip_token = secrets.ipinfo_token
weather_token = secrets.weather_token
hour = int(datetime.now().time().strftime("%H"))
time = datetime.now().time().strftime("%H:%M")

# get my ip address using httpbin.org
my_ip = requests.get(url = "http://httpbin.org/ip").json()["origin"]

# get the city I'm in using ipinfo.io's library - this means it only works on wifi
handler = ipinfo.getHandler(ip_token)
city = handler.getDetails(my_ip).city

# create the parameters we're using for our weather api call
weatherUrl = "http://api.openweathermap.org/data/2.5/weather"
weatherParams = dict(q = city, APPID = weather_token)

# call the weather api and get back the current weather type
weather = requests.get(url = weatherUrl, params = weatherParams)
weather = weather.json()["weather"][0]["main"]

# current weather can be one of:
# Thunderstorm, Drizzle, Rain, Snow, Mist, Smoke, Haze, Dust, Fog, Sand, Ash, Squall, Tornado, Clear, Clouds
# These, combined with the time, match to different radios, as outlined in the dictionaries below

weatherTypes = {        #energy, happy
        "Thunderstorm" : [2, -1],
        "Drizzle" : [-1, -1],
        "Rain" : [-1, -2],
        "Snow" : [0, 0],
        "Mist" : [-1, -1],
        "Smoke" : [1, -2],
        "Haze" : [0, -2],
        "Dust" : [0, -2],
        "Fog" : [-1, -1],
        "Sand" : [1, 0],           
        "Ash" : [2, -2],            
        "Squall" : [1, -1],         
        "Tornado" : [2, -2],
        "Clear" : [1, 1],
        "Clouds" : [-1, -1] }

dayTimes = {    #energy, happy
        "Dawn" : [-1, 1],
        "Morning" : [1, 1],
        "Afternoon" : [0, 0],
        "Dusk" : [0, 1],
        "Night" : [-1, -1] }

stations = {"Cozy Fireplace" :      "39031",
            "Disney" :              "38335",
            "Kids Pop" :            "30751",
            "Surf Songs" :          "37081",
            "Pop Latin" :           "36791",
            "Acoustic Afternoon" :  "38435",
            "Gospel" :              "39071",
            "Summer Afternoon" :    "37645",
            "Func" :                "30831",
            "Disco" :               "30841",           
            "Indie" :               "42242",            
            "Folk" :                "42262",         
            "Classical" :           "30661",
            "Pop" :                 "42062",
            "Dubstep" :             "38215",
            "Country Blues" :       "36801",            
            "Country" :             "42282",            
            "Jazz" :                "31031",            
            "Film Scores" :         "30701",            
            "Hip Hop" :             "30991",            
            "Blues" :               "30921",            
            "Sad Songs" :           "39051",            
            "R&B" :                 "30881",            
            "Soul" :                "30861",            
            "Metal" :               "30901"}


                # energy ->
stationMatrix = [["Cozy Fireplace",     "Disney",       "Kids Pop",             "Surf Songs",   "Pop Latin" ],   
                 ["Acoustic Afternoon", "Gospel",       "Summer Afternoon",     "Func",         "Disco"     ],   
                 ["Indie",              "Folk",         "Classical",            "Pop",          "Dubstep"   ],   #   ^
                 ["Country Blues",      "Country",      "Jazz",                 "Film Scores",  "Hip Hop"   ],   #   |
                 ["Blues",              "Sad Songs",    "R&B",                  "Soul",         "Metal"     ]]   # happy

#get our time modifier
timeName = ""
if(hour < 5):
    timeName = "Night"
elif (hour < 8):
    timeName = "Dawn"
elif (hour < 12):
    timeName = "Morning"
elif (hour < 17):
    timeName = "Afternoon"
elif (hour < 20):
    timeName = "Dusk"
else:
    timeName = "Night"

timeMod = dayTimes[timeName]
print(timeMod)

#get our weather modifier
weatherMod = weatherTypes[weather]
print(weatherMod)

#combine our time and weather modifier with center space, [2,2]
modifier = [2, 2]
modifier[0] += timeMod[0]
modifier[1] -= timeMod[1]
modifier[0] += weatherMod[0]
modifier[1] -= weatherMod[1]

#make sure modifier is within the 1-5 (0-4) range
if(modifier[0] > 4):
    modifier[0] = 4
elif (modifier[0] < 0):
    modifier[0] = 0

if(modifier[1] > 4):
    modifier[1] = 4
elif (modifier[1] < 0):
    modifier[1] = 0
print(modifier)

stationName = stationMatrix[modifier[1]][modifier[0]]
stationNumber = stations[stationName]
    
# get the json of the radio information from deezer
deezer_radio = requests.get(url = "https://api.deezer.com/radio/{}/tracks?output=json".format(stationNumber)).json()
songData = deezer_radio["data"]

# get the spotify uri for the songs (and print them out as well)
songURIs = []
for songDatum in songData:
    response = requests.get(url = "https://api.spotify.com/v1/search?q=track%3A{}%20artist%3A{}&type=track&limit=1".format(songDatum["title"], songDatum["artist"]["name"]),
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(spotify_token)
            }
    ).json()
    if (len(response["tracks"]["items"]) > 0):
        songURIs.append(response["tracks"]["items"][0]["uri"])
                    
    print(songDatum["title"])


# create playlist

response = requests.post(
    "https://api.spotify.com/v1/users/{}/playlists".format(spotify_id),
    data=json.dumps({
        "name": "{} in {} at {}".format(weather, city, timeName),
        "description": "This playlist was created by Weathermuse to give you songs matching the current time and weather, wherever you are! The music is from the Deezer station, \"{}\"".format(stationName),
        "public": True
    }),
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(spotify_token)
    }
)

response_json = response.json()
playlist_id = response_json["id"]

#populate the songs of the playlist
requests.post(
    "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id),
    json.dumps(songURIs),
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(spotify_token)
    })
