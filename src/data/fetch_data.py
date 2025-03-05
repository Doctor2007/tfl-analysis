import pandas as pd
import requests as req
import random as rng
import datetime as dt


def get_route(start: str, end: str, date_time = 'now') -> dict:
    if not isinstance(date_time, str):
        raise ValueError('Datetime has to be in str format')

    url = f'https://api.tfl.gov.uk/Journey/JourneyResults/{start}/to/{end}'

    params = {
        'mode': 'tube',
        "dateTime": date_time,
        'traffic': 'true',
    }

    response = req.get(url, params=params)

    if response.status_code != 200:
        print(f"API Error for {start} to {end} on {date_time}")
        print(f"Response content: {response.text[:200]}...")
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

def get_stop_points(stop_points, num_stops=2):
    if len(stop_points) < num_stops:
        raise ValueError('Not enough stops in the stop_points database')
    return rng.sample(stop_points, num_stops)

def gen_dates(num_days = 30):
    today = dt.datetime.now()
    dates = []

    for i in range(num_days):
        next_date = today + dt.timedelta(days=i)
        formatted_date = next_date.strftime('%Y-%m%dT09:00:00')
        dates.append(formatted_date)

    return dates

def get_journey_data(n_data = 30):
    dates = gen_dates(n_data)
    random_stops = get_stop_points(fetch_stop_points())
    start = random_stops[0]['name']
    end = random_stops[1]['name']

    route_data = {}
    for item in dates:
        route_data[item] = get_route(start, end, item)


    print(route_data)

    df = pd.DataFrame(route_data)
    print(df)

get_journey_data(2)