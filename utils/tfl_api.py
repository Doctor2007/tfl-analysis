import pandas as pd
import requests as req
import os
import concurrent.futures
import time
import random as rng


API_KEY = 'your_api_key'

n_errors = 0

data = pd.read_csv('data/processed/processed1000.csv', dtype={'Start time': str})

start_journey = data['start_coordinates']
end_journey = data['end_coordinates']
time_journey = data['Start time']
date_journey = data['New Start date']

# little thinking about time complexity
# tfl api limits requests 500/min
# 
# 500 // 60 = 8 (8.3) requests per second
# it takes about 2.2s to process 10 rows without time.sleep() with 10 workers
# so each worker needs 2.2s to process a request

# def time_complexity(df):

#     pass





def get_tfl_data(origin, destination, journey_date=None, journey_time=None, timeIs='departing', journeyPreference='leasttime', mode='public_transport', max_retries=3):
        url = f'https://api.tfl.gov.uk/Journey/JourneyResults/{origin}/to/{destination}'

        if mode =='public_transport':
            mode = 'bus,overground,tube,coach,dlr,tram,elizabeth-line,replacement-bus'

        params = {
            'app_key': API_KEY,
            'date': journey_date,
            'time': journey_time, 
            'timeIs': timeIs, 
            'journeyPreference': journeyPreference,
            'mode': mode
        }

        response = None
        retries = 0

        while retries <= max_retries:
            response = req.get(url, params=params)
            if response.status_code == 200:
                time.sleep(rng.uniform(0.05, 0.1))
                break
            else:
                pass
                # print(f'Retry N{retries}')
            if response.status_code == 429:
                time.sleep(rng.uniform(1, 5))
            else:
                time.sleep(rng.uniform(0.1, 0.5))

            
            # if response is NOT very feel
            # print(f"API returned: {response.status_code}")
            # print(f"API returned error {response.status_code} for {origin} to {destination}")
            # print(f"Request URL: {response.url}")

            # print(f'Error {response.status_code}')
            retries += 1

            if retries == max_retries:
                # global n_errors
                # n_errors += 1
                return None
        
        if response is None:
            return None

        data = response.json()

        # if response is very feel
        return data["journeys"][0]["duration"]


def run_tfl_data(data, start_journey, end_journey):
    def get_journey_duration(i):
        if i % 100 == 0:
            print(f'{i} is done')
        public_duration = get_tfl_data(
            origin=start_journey.iloc[i], 
            destination=end_journey.iloc[i], 
            journey_time=time_journey.iloc[i],
            journey_date=date_journey.iloc[i],
            mode='public_transport'

        )
        cycling_duration = get_tfl_data(
            origin=start_journey.iloc[i], 
            destination=end_journey.iloc[i], 
            journey_time=time_journey.iloc[i],
            mode='cycle'
        )

        return {
            'public_transport': public_duration,
            'cycling': cycling_duration
        }
    

    actual_cpu_count = os.cpu_count()
    desired_cpu_count = actual_cpu_count - 1

    indices = range(len(data)) 

    with concurrent.futures.ThreadPoolExecutor(max_workers=desired_cpu_count) as executor:
        duration_values = list(
            executor.map(get_journey_duration, indices)
        )

    return duration_values

if __name__ == '__main__':
    start = time.time()
    travel_times = pd.DataFrame(run_tfl_data(data, start_journey, end_journey))
    end = time.time()

    print(f"Total runtime of the program is {end - start} seconds")
    print(os.cpu_count())
    dataset = pd.concat([data.reset_index(drop=True), travel_times.reset_index(drop=True)], axis=1)
    
    print(dataset.head())

    print("Processing complete")

    print(f'{n_errors} number of errors')

    dataset.to_csv('data/processed/api_processed/sample_1000.csv')

    