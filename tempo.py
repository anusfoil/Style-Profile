from utils import *
import matplotlib.pyplot as plt


def calculate_tempo(match, level='ibi'):
    """plot tempo on beat or measure level"""
    match_beats = match[match['score_time'].apply(float.is_integer)]  # select the ones on the beat
    match_beats = match[match['error_index'] == 0] # not including extra notes 
    # TODO: repeats? the same score beat but different events

    beat_onsets = match_beats.groupby("score_time").min()
    # interpolate the missing beats (beats without note event)
    beat_onsets = beat_onsets.reindex(range(0, int(beat_onsets.index.max())+1))
    beat_onsets = beat_onsets.interpolate()['onset_time']

    # set the IBI to original data
    match = match.set_index('score_time', drop=False)
    match['ibi'] = beat_onsets - beat_onsets.shift(1)
    match = match.set_index('ID', drop=False)
    # calculate the local tempo using ibi
    match['tempo'] = 60 / match['ibi'] 

    # TODO: outlier detection... some obvious wrong tempo / ibi because of repeat gaps

    return match

def tempo_attributes():
    return {}

def plot_tempo(match):
    plt.step(match['score_time'], match['tempo'])
    plt.grid()
    plt.show()
    return 

if __name__ == "__main__":
    match = parse_match("../Datasets/ATEPP-1.1/Johann_Sebastian_Bach/Das_Wohltemperierte_Klavier_Book2/Book_2,_BWV_870-893:_Prelude_in_A_minor_BWV_889/02966_match.txt")
    match = calculate_tempo(match)
    plot_tempo(match)