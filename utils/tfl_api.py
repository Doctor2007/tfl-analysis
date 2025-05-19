import pandas as pd
import requests as req
import os
import csv
import concurrent.futures
import time
import random as rng
from loguru import logger

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

        retries = 0

        while retries <= max_retries:
            response = req.get(url, params=params)
            if response.status_code == 429:
                logger.info('Sleeping for 5s...')
                time.sleep(5)
            elif response.status_code == 404:
                time.sleep(rng.uniform(0.1, 0.5))
                logger.info('Sleeping for 0.3s...')
            elif response.status_code == 200:
                time.sleep(rng.uniform(0.05, 0.1))
                break
            else:
                logger.info('Sleeping for 4s...')
                time.sleep(4)
            

            
            # if response is NOT very feel
            retries += 1

            logger.info(f'Retrying... [{retries}]/[{max_retries}]')

            if retries == max_retries:
                logger.error(f"API returned: {response.status_code}")
                logger.error(f"Request URL: {response.url}")
                
                global n_errors
                n_errors += 1
                return None

        data = response.json()

        # if response is very feel
        return data["journeys"][0]["duration"]


def run_tfl_data(data, start_journey, end_journey):
    def get_journey_duration(i):
        if i % 100 == 0:
            logger.info(f'{i} is done')
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
        logger.info('Finished API calls')
        df_durations = pd.DataFrame(duration_values)
        logger.info('Converted to df')

    return df_durations

if __name__ == '__main__':

    logger.remove()
    logger.add("logs/tfl_api.log", level="INFO", mode="w")

    API_KEY = 'your_api_key'

    n_errors = 0

    data = pd.read_csv('data/processed/cleaned_data.csv', dtype={'Start time': str}, index_col=False)

    start_journey = data['start_coordinates']
    end_journey = data['end_coordinates']
    time_journey = data['Start time']
    date_journey = data['New Start date']

    SAMPLE_SIZE = 100
    data_sample = data.head(SAMPLE_SIZE).copy().astype(str)

    logger.info("Starting API calls")
    start = time.time()
    travel_times = run_tfl_data(data_sample, start_journey, end_journey)
    logger.info("Finished API calls")
    end = time.time()
    logger.info(f"Total runtime of the program is {end - start} seconds")

    dataset = pd.concat([data.reset_index(drop=True), travel_times.reset_index(drop=True)], axis=1)
    logger.info(f"Concating complete")
    start_saving = time.time()
    dataset.to_feather(f'data/processed/api_processed/sample_{SAMPLE_SIZE}.feather')
    end_saving = time.time()
    logger.info(f"Total runtime of the program-saving is {end_saving - start_saving} seconds")
    logger.warning(f'{n_errors} number of errors')

    
