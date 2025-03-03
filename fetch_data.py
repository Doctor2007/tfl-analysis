import pandas as pd
import requests as req
import random as rng

def get_route(start, end):
    url = f'https://api.tfl.gov.uk/Journey/JourneyResults/{start}/to/{end}'

    params = {
        'mode': 'tube',
        "dateTime": "now",
        'traffic': 'true',
    }

    response = req.get(url, params=params)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")
    
    journey_data = response.json()


    result = {
        'start_platform': start,
        'end_platform': end,
        'duration_minutes': 0,
        'intermediate_platforms': [],
        'interchange_stations': []
    }
    
    if not journey_data.get('journeys'):
        return result
    
    # best journey option
    journey = journey_data['journeys'][0]
    result['duration_minutes'] = journey.get('duration', 0)
    
    # Extract stations where we change lines
    legs = journey.get('legs', [])
    
    # Simple loop to extract interchanges (stations where we change)
    prev_arrival = None
    for leg in legs:
        departure = leg.get('departurePoint', {}).get('commonName', '')
        
        if prev_arrival and departure == prev_arrival:
            result['interchange_stations'].append(departure)
        
        prev_arrival = leg.get('arrivalPoint', {}).get('commonName', '')
    
    return result


def fetch_stop_points():
    url = 'https://api.tfl.gov.uk/StopPoint/Search'
    params = {
        'modes': 'tube',
        'query': 'station',
    }

    response = req.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching stop points: {response.status_code}")
    data = response.json()
    stop_points = data['matches']
    return stop_points

stop_points = fetch_stop_points()

def get_stop_points(stop_points, num_stops=2):
    if len(stop_points) < num_stops:
        raise ValueError('Not enough stops in the stop_points database')
    return rng.sample(stop_points, num_stops)

random_stops = get_stop_points(stop_points)

start = random_stops[0]['name']
end = random_stops[1]['name']

route_info = get_route(start, end)
print(route_info)