import numpy as np
from utils import *
from tempo import *

def calculate_duration_percentage(match):
    """take the estimated tempo and find the expected duration of each note, 
        then find the articulation ratio (how full is the duration of the note) """
    match.fillna(method='bfill', inplace=True)
    match.fillna(method='ffill', inplace=True)

    expected_dur = match['score_dur'] * match['ibi']
    match['duration_percentage'] = (match['offset_time'] - match['onset_time']) / expected_dur

    return match

def get_kor(e1, e2):

    kot = e1['offset_time'] - e2['onset_time']
    ioi = e2['onset_time'] - e1['onset_time']

    return kot / ioi

def calculate_key_overlap_ratio(match):
    """
    B.Repp: Acoustics, Perception, and Production of Legato Articulation on a Digital Piano

    how to find the 'preceeding tone'?
    - which melody line? is it hand-specific or voice-specific?
    - what if the previous tone is already overlapping in terms of score time?

    if the prev note's offset is on the next note's onset, and they are in the same voice, then we calculate KOR for them
    """

    match['score_offset'] = match['score_time'] + match['score_dur']

    match['key_overlap_ratio'] = np.nan

    # consider the note transition by each voice
    for voice in match['voice'].unique():
        match_voiced = match[match['voice'] == voice]
        for i, row in match_voiced.iterrows():
            if i == len(match_voiced) - 1:
                break
            nextrow = match_voiced.iloc[i + 1]

            # KOR for general melodic transitions
            if (row['score_offset'] == nextrow['score_time']):
                original_position = match[match['ID'] == row['ID']].index
                match.at[original_position, 'key_overlap_ratio'] = get_kor(row, nextrow)
            
            # KOR for repeated notes 
            if (row['spelled_pitch'] == nextrow['spelled_pitch']):
                original_position = match[match['ID'] == row['ID']].index
                match.at[original_position, 'kor_repeated'] = get_kor(row, nextrow)                

            # KOR for legato notes

            # KOR for staccato notes
            if row['articulation'] == 'staccato':
                original_position = match[match['ID'] == row['ID']].index
                match.at[original_position, 'kor_staccato'] = get_kor(row, nextrow)                  


    return match

def articulation_attributes(match):
    """
    - duration contrast percentage (fullness)
    - key overlap ratio (legato, staccato, repeated)
    """

    match = calculate_duration_percentage(match)
    match = calculate_key_overlap_ratio(match)

    return {
        "sp_duration_percentage": match[match['duration_percentage'] != np.inf]['duration_percentage'].mean(),
        "sp_key_overlap_ratio": match['key_overlap_ratio'].mean(),
        # "sp_kor_legato": ,
        "sp_kor_staccato": match['kor_staccato'].mean(),
        # "sp_kor_repeated": 
    }

if __name__ == "__main__":
    match = parse_match("../Datasets/ATEPP-1.1/Johann_Sebastian_Bach/Das_Wohltemperierte_Klavier_Book2/Book_2,_BWV_870-893:_Prelude_in_A_minor_BWV_889/02966_match.csv")
    # match = calculate_tempo(match)
    match = calculate_key_overlap_ratio(match)
