import os, sys, copy
import numpy as np
import pretty_midi
import matplotlib.pyplot as plt

from tqdm import tqdm
from utils import * 

ATTRIBUTES = ["sp_async_delta", "sp_async_cor_onset", "sp_async_cor_vel"]

def get_async_groups(match):
    """returns the chords or intervals that has the same metrical start time"""
    match = match[match['error_index'] == "0"]
    onset_groups = match.groupby(['score_time']).groups
    onset_groups = {k:v for k, v in onset_groups.items() if len(v) > 1}
    return onset_groups

def async_attributes(onset_groups, match, v=False):
    tol_delta, tol_cor, tol_cor_vel = 0, 0, 0
    for _, indices in onset_groups.items():
        onset_times = match.iloc[indices]['onset_time'].astype(float)
        delta = onset_times.max() - onset_times.min()
        if delta > 5: # some notes have the same score time because of repeat, but they are not actually from the same chord
            continue 
        tol_delta += delta 

        midi_pitch = match.iloc[indices]['spelled_pitch'].apply(pretty_midi.note_name_to_number)
        midi_pitch = midi_pitch - midi_pitch.min() # min-scaling
        onset_times = onset_times - onset_times.min()
        cor = np.corrcoef(midi_pitch, onset_times)[0, 1]
        tol_cor += (0 if np.isnan(cor) else cor)
    
        midi_vel = match.iloc[indices]['onset_velocity'].astype(float)
        midi_vel = midi_vel - midi_vel.min()
        cor = np.corrcoef(midi_vel, onset_times)[0, 1]
        tol_cor_vel += (0 if np.isnan(cor) else cor)

    return {
        "sp_async_delta": (tol_delta / len(onset_groups)),
        "sp_async_cor_onset": -(tol_cor / len(onset_groups)),
        "sp_async_cor_vel": -(tol_cor_vel / len(onset_groups))
    }


def compute_all_attributes(rerun=False):

    if os.path.exists("attributes.csv") and (not rerun):
        return pd.read_csv("attributes.csv")

    meta_csv = pd.read_csv(DATA_CSV)
    meta_attributes = copy.deepcopy(meta_csv)
    
    for attribute in ATTRIBUTES:
        meta_attributes[attribute] = np.nan
    for idx, row in meta_attributes.iterrows():
        match_file = f"{DATA_DIR}/{row['midi_path'][:-4]}_match.txt"
        if os.path.exists(match_file):
            match = parse_match(match_file)
            onset_groups = get_async_groups(match)
            result = async_attributes(onset_groups, match)
            for k, v in result.items():
                meta_attributes.at[idx, k] = v
    
    meta_attributes.to_csv("attributes.csv")
    return meta_attributes


if __name__ == "__main__":

    meta_attributes = compute_all_attributes()

    labels = meta_attributes['artist'].unique()
    attribute_by_label = meta_attributes.groupby('artist').mean()

    X_axis = np.arange(len(labels))
    plt.bar(X_axis - 0.4, attribute_by_label["sp_async_delta"], 0.4, label = 'avg_delta')
    plt.bar(X_axis, attribute_by_label["sp_async_cor_onset"], 0.4, label = 'avg_cor_onset')
    plt.bar(X_axis + 0.4, attribute_by_label["sp_async_cor_vel"], 0.4, label = 'avg_cor_vel')

    plt.xticks(X_axis, labels, rotation = 45)
    plt.legend()
    plt.grid()
    plt.show()
    pass