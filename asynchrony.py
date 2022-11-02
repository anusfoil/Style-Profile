import os, sys, copy
import numpy as np
import pretty_midi
import matplotlib.pyplot as plt

from tqdm import tqdm
from utils import * 

def get_async_groups(match):
    """returns the chords or intervals that has the same metrical start time"""
    match = match[match['error_index'] == "0"]
    onset_groups = match.groupby(['score_time']).groups
    onset_groups = {k:v for k, v in onset_groups.items() if len(v) > 1}
    return onset_groups

def async_attributes(onset_groups, match, v=False):
    tol_delta, tol_cor = 0, 0
    for _, indices in onset_groups.items():
        onset_times = match.iloc[indices]['onset_time'].astype(float)
        delta = onset_times.max() - onset_times.min()
        if delta > 5: # some notes have the same score time because of repeat, but they are not actually from the same chord
            continue 
        tol_delta += delta 
        if v:
            print(indices)
            print(onset_times.max(), onset_times.min())

        midi_pitch = match.iloc[indices]['spelled_pitch'].apply(pretty_midi.note_name_to_number)
        midi_pitch = midi_pitch - midi_pitch.min()
        onset_times = onset_times - onset_times.min()
        cor = np.corrcoef(midi_pitch, onset_times)[0, 1]
        tol_cor += (0 if np.isnan(cor) else cor)

    return {
        "avg_delta": (tol_delta / len(onset_groups)),
        "avg_cor": -(tol_cor / len(onset_groups))
    }


def compute_all_attributes(category="artist"):

    if os.path.exists("attributes.csv"):
        return pd.read_csv("attributes.csv")

    meta_csv = pd.read_csv(DATA_CSV)
    meta_attributes = copy.deepcopy(meta_csv)
    meta_attributes['avg_delta'] = np.nan
    meta_attributes['avg_cor'] = np.nan
    midi_list = meta_csv['midi_path']
    for idx, row in meta_attributes.iterrows():
        match_file = f"{DATA_DIR}/{row['midi_path'][:-4]}_match.txt"
        if os.path.exists(match_file):
            match = parse_match(match_file)
            onset_groups = get_async_groups(match)
            result = async_attributes(onset_groups, match)
            for k, v in result.items():
                meta_attributes.at[idx, k] = v
    
    return meta_attributes


if __name__ == "__main__":

    meta_attributes = compute_all_attributes()


    category_labels = []
    category_attributes = copy.deepcopy(empty_attributes)
    for label in tqdm(meta_csv['composer'].unique()):
        print(label)
        label_attributes = copy.deepcopy(empty_attributes)
        midi_list = meta_csv[meta_csv['composer'] == label]['midi_path']
        for perf in (midi_list):
            match_file = f"{DATA_DIR}/{perf[:-4]}_match.txt"
            if os.path.exists(match_file):
                match = parse_match(match_file)
                onset_groups = get_async_groups(match)
                result = async_attributes(onset_groups, match)
                for attribute in result.keys():
                    label_attributes[attribute].append(result[attribute])

        print(f"num. pieces: {len(label_attributes['avg_delta'])}")
        if len(label_attributes['avg_delta']) > 10:
            category_labels.append(label.split(" ")[-1])
            for k, v in label_attributes.items():
                category_attributes[k].append(sum(v) / len(v))
                print(sum(v) / len(v))


    X_axis = np.arange(len(category_labels))
    plt.bar(X_axis - 0.2, category_attributes["avg_delta"], 0.4, label = 'avg_delta')
    plt.bar(X_axis + 0.2, category_attributes["avg_cor"], 0.4, label = 'avg_cor')

    plt.xticks(X_axis, category_labels, rotation = 45)
    plt.legend()
    plt.grid()
    plt.show()
    pass