import numpy as np
from utils import *
from tempo import *

def calculate_articulation_ratio(match):
    """take the estimated tempo and find the expected duration of each note, 
        then find the articulation ratio (how full is the duration of the note) """
    match.fillna(method='bfill', inplace=True)
    match.fillna(method='ffill', inplace=True)

    expected_dur = match['score_dur'] * match['ibi']
    match['articulation_ratio'] = (match['offset_time'] - match['onset_time']) / expected_dur

    return match

def articulation_attributes(match_with_tempo):

    match = calculate_articulation_ratio(match_with_tempo)
    match = match[match['articulation_ratio'] != np.inf]
    return {
        "sp_articulation_ratio": match['articulation_ratio'].mean()
    }

if __name__ == "__main__":
    match = parse_match("../Datasets/ATEPP-1.1/Johann_Sebastian_Bach/Das_Wohltemperierte_Klavier_Book2/Book_2,_BWV_870-893:_Prelude_in_A_minor_BWV_889/02966_match.txt")
    match = calculate_tempo(match)
    calculate_articulation_ratio(match)
