import random
MAX_TIME_IN_SECONDS = 10
MIN_TIME_IN_SECONDS = 1


def get_random_time_interval_to_sleep():
    return random.randint(MIN_TIME_IN_SECONDS, MAX_TIME_IN_SECONDS)
