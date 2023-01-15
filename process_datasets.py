import copy
import pandas as pd
import numpy as np
from tqdm import tqdm
from ESP import ExpressionStyleProfile
from params import *



def process_ATEPP():
    """process the entire ATEPP dataset with ESP and write the attributes"""

    meta_csv = pd.read_csv(ATEPP_DATA_CSV)
    meta_attributes = copy.deepcopy(meta_csv)

    # only include those who have a valid alignment
    meta_attributes = meta_attributes[~meta_attributes['valid_match'].isna()]
    
    for attribute in ATTRIBUTES:
        meta_attributes[attribute] = np.nan
    for idx, row in tqdm(meta_attributes.iterrows()):

        esp = ExpressionStyleProfile(
            f"{ATEPP_DATA_DIR}/{row['midi_path']}",
            f"{ATEPP_DATA_DIR}/{row['score_path']}",
            # match_file=f"{ATEPP_DATA_DIR}/{row['valid_match']}"
            )

        attributes = esp.get_attributes()

        for k, v in attributes.items():
            meta_attributes.at[idx, k] = v
    
        meta_attributes.to_csv(ATEPP_ATTRIBUTES, index=False)

    return meta_attributes


def process_ASAP():
    """process the entire ASAP dataset with ESP and write the attributes"""

    meta_csv = pd.read_csv(ATEPP_DATA_CSV)
    meta_attributes = copy.deepcopy(meta_csv)

    # only include those who have a valid alignment
    meta_attributes = meta_attributes[~meta_attributes['valid_match'].isna()]
    
    for attribute in ATTRIBUTES:
        meta_attributes[attribute] = np.nan
    for idx, row in tqdm(meta_attributes.iterrows()):
        # if ("Barcarolle_Op._60" in match_file) or ("Barcarolle_in_F-Sharp_Major,_Op._60" in match_file):
        #     continue

        esp = ExpressionStyleProfile(
            f"{ATEPP_DATA_DIR}/{row['midi_path']}",
            f"{ATEPP_DATA_DIR}/{row['score_path']}",
            match_file=f"{ATEPP_DATA_DIR}/{row['valid_match']}")

        attributes = esp.get_attributes()

        for k, v in attributes.items():
            meta_attributes.at[idx, k] = v
    
        meta_attributes.to_csv("asap_attributes.csv", index=False)

    return meta_attributes

def process_vienna422():
    """process the entire vienna4*22 dataset with ESP and write the attributes"""

    meta_csv = pd.read_csv(ATEPP_DATA_CSV)
    meta_attributes = copy.deepcopy(meta_csv)

    # only include those who have a valid alignment
    meta_attributes = meta_attributes[~meta_attributes['valid_match'].isna()]
    
    for attribute in ATTRIBUTES:
        meta_attributes[attribute] = np.nan
    for idx, row in tqdm(meta_attributes.iterrows()):
        # if ("Barcarolle_Op._60" in match_file) or ("Barcarolle_in_F-Sharp_Major,_Op._60" in match_file):
        #     continue

        esp = ExpressionStyleProfile(
            f"{ATEPP_DATA_DIR}/{row['midi_path']}",
            f"{ATEPP_DATA_DIR}/{row['score_path']}",
            match_file=f"{ATEPP_DATA_DIR}/{row['valid_match']}")

        attributes = esp.get_attributes()

        for k, v in attributes.items():
            meta_attributes.at[idx, k] = v
    
        meta_attributes.to_csv("asap_attributes.csv", index=False)

    return meta_attributes


if __name__ == "__main__":

    # esp = ExpressionStyleProfile("examples/mozart_match.csv", "examples/mozart.xml")
    # esp.get_attributes()
    # print(esp)

    process_ATEPP()