from linedata import platforms, line_segments
from environment import Environment

def random_train_generator(env:Environment):
    max_trains = len(platforms)
    import random
    rnd_number_of_trains = random.randint(1, max_trains)
    # create trains at random but unique platforms
    train_platforms = random.sample(platforms, rnd_number_of_trains)
    return train_platforms

def random_train_generator(env:Environment, number_of_trains:int):
    import random
    # create trains at random but unique platforms
    train_platforms = random.sample(platforms, number_of_trains)
    return train_platforms