import os, copy
import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm
from asynchrony import *
from tempo import *
from articulation import *
from dynamics import *
from utils import * 

ATTRIBUTES = ["sp_async_delta", "sp_async_cor_onset", "sp_async_cor_vel",
                "sp_articulation_ratio",
                "sp_tempo_std",
                "sp_dynamics_agreement", "sp_dynamics_consistency_std"
                ]

def compute_all_attributes(rerun=False):

    if os.path.exists("attributes.csv") and (not rerun):
        return pd.read_csv("attributes.csv")

    meta_csv = pd.read_csv(DATA_CSV)
    meta_attributes = copy.deepcopy(meta_csv)
    
    for attribute in ATTRIBUTES:
        meta_attributes[attribute] = np.nan
    for idx, row in tqdm(meta_attributes.iterrows()):
        match_file = f"{DATA_DIR}/{row['midi_path'][:-4]}_match.csv"
        # if ("Barcarolle_Op._60" in match_file) or ("Barcarolle_in_F-Sharp_Major,_Op._60" in match_file):
        #     continue
        if os.path.exists(match_file):
            match = parse_match(match_file)
            if match is not None:
                """asynchorny attributes"""
                onset_groups = get_async_groups(match)
                result = async_attributes(onset_groups, match)

                """tempo_attributes"""
                result.update(tempo_attributes(match))

                """articulation_attributes"""
                result.update(articulation_attributes(match))

                """dynamics_attributes"""
                result.update(dynamics_attributes(match))
                for k, v in result.items():
                    meta_attributes.at[idx, k] = v
    
    meta_attributes.to_csv("attributes.csv", index=False)
    return meta_attributes


if __name__ == "__main__":

    meta_attributes = compute_all_attributes(rerun=True)
    hook()

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