import pandas as pd
import requests as req
import os
import concurrent.futures
import time
import random as rng
from loguru import logger


# ! DISABLE WINDOWS DEFENDER: it starts blocking if there are to many requests
# little thinking about time complexity
# tfl api limits requests 500/min
# 
# 500 // 60 = 8 (8.3) requests per second
# due to this I'll sample 10% of the data
# which brings the processing speed to around 6 hours
# There are definately ways to improve it, but I'm using pretty generous sleep times, so that I don't have to write extra complex error logic


def get_tfl_data(origin, destination, journey_date=None, journey_time=None, timeIs='departing', journeyPreference='leasttime', mode='public_transport', max_retries=3):
        """
        ! REQUIRED:
            origin - start journey point: coordinates (latitude, longitude)
            destination - end journey point: coordinates (latitude, longitude)
        * RECOMMENDED:
            journey_date - date that journey took place: %Y%m%d
            journey_time - time that journey took place: %H%M
        
        DEFAULTS:
            timeIs - can do departing/arriving: departing
            journeyPreference - can select various methods: leasttime
            mode - can select specific mode or modes
                -> I concatenated all 'public transport'
                another input I use is cycle
            max_retries - retries upon error: 3
            ! I do not recomment changing retries without changing sleep times

            returns: int(duration)
        """
        url = f'https://api.tfl.gov.uk/Journey/JourneyResults/{origin}/to/{destination}'

        if mode =='public_transport':
            mode = 'bus,overground,tube,coach,dlr,tram,elizabeth-line,replacement-bus'

        params = {
            # api key can be created in api-portal for free
            'app_key': API_KEY,
            'date': journey_date,
            'time': journey_time, 
            'timeIs': timeIs, 
            'journeyPreference': journeyPreference,
            'mode': mode
        }

        retries = 0

        # TODO: Create a better retry logic (not necessary for research)
        while retries <= max_retries:
            response = req.get(url, params=params)
            if response.status_code == 429:
                logger.info('Sleeping for 10s...')
                time.sleep(10)
            elif response.status_code == 404:
                time.sleep(rng.uniform(0.1, 0.5))
                logger.info('Sleeping for 0.3s...')
            elif response.status_code == 200:
                time.sleep(rng.uniform(0.05, 0.1))
                break
            else:
                logger.info('Sleeping for 4s...')
                time.sleep(4)
            

            
            # if Error
            retries += 1

            logger.info(f'Retrying... [{retries}]/[{max_retries}]')

            if retries == max_retries:
                logger.error(f"API returned: {response.status_code}")
                logger.error(f"Request URL: {response.url}")
                
                # this is for trouble shooting resons, but might save a little bit of time if avoiding
                global n_errors
                n_errors += 1
                return None

        data = response.json()

        # if response is very feel
        return data["journeys"][0]["duration"]


def run_tfl_data(data, start_journey, end_journey):
    def get_journey_duration(i):
        if i % 100 == 0:
            # to see some progress getting done, but not overflooding the log
            logger.info(f'{i} is done')

        # TODO: Maybe might be more pretty if classes are used (not necessary for research)
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
            journey_date=date_journey.iloc[i],
            mode='cycle'
        )

        return {
            'public_transport': public_duration,
            'cycling': cycling_duration
        }
    
    # I want to leave 1 so that computer can still be functional
    actual_cpu_count = os.cpu_count()
    desired_cpu_count = actual_cpu_count - 1


    # This creates a basic 1 to x thing, so that map function can run trough them
    indices = range(len(data)) 

    with concurrent.futures.ThreadPoolExecutor(max_workers=desired_cpu_count) as executor:
        # I wanted to implement a tqdm (progress bar), but since I'm using map, it treats it as a singular process
        duration_values = list(
            executor.map(get_journey_duration, indices)
        )
        logger.info('Finished API calls')
        df_durations = pd.DataFrame(duration_values)
        logger.info('Converted to df')

    return df_durations

# That's if someone wanted to export the functions and run this elsewhere
# Might look like AI, but I remember it since my other independant project where AI showed me this feature
if __name__ == '__main__':

    # removes active logger and ovewrite the file existing
    logger.remove()
    logger.add("logs/tfl_api.log", level="INFO", mode="w")

    API_KEY = '...'

    n_errors = 0

    data = pd.read_csv('data/processed/cleaned_data_sample10.csv', dtype={'Start time': str}, index_col=False)

    # ? Again Class might be more pretty
    start_journey = data['start_coordinates']
    end_journey = data['end_coordinates']
    time_journey = data['Start time']
    date_journey = data['New Start date']

    # Tracks how long it took to run
    logger.info("Starting API calls")
    start = time.time()
    travel_times = run_tfl_data(data, start_journey, end_journey)
    logger.info("Finished API calls")
    end = time.time()
    logger.info(f"Total runtime of 6the program is {end - start} seconds")

    dataset = pd.concat([data.reset_index(drop=True), travel_times.reset_index(drop=True)], axis=1)
    logger.info(f"Concating complete")
    # Tracks how long it took to save
    # I tried using CSV first, but it froze and memory was overwhelmed
    # ! DO NOT USE CSV
    # Parquet works the same, might want to download an extension to view it though
    start_saving = time.time()
    SAMPLE_SIZE = 10 # %
    dataset.to_parquet(f'data/processed/api_processed/sample_{SAMPLE_SIZE}.parquet')
    end_saving = time.time()
    logger.info(f"Total runtime of the program-saving is {end_saving - start_saving} seconds")
    logger.warning(f'{n_errors} number of errors')