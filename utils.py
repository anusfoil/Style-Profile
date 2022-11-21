import os, re, glob
import pandas as pd
from tqdm import tqdm
import numpy as np
import partitura as pt

import hook

DATA_CSV = "../Datasets/ATEPP-1.1/ATEPP-metadata-1.2.csv"
DATA_DIR = "../Datasets/ATEPP-1.1/"

def get_measure(note_ID):
    note_info = note_ID.split("-")
    try:
        return int(note_info[1])
    except:
        return -1

def parse_match(match_file, use_txt=False):
    """returns: pandas dataframe with matched notes information
    Note: the missing notes are not included. 
    """

    if (not use_txt) and (match_file[-4:] == ".csv"):
        return pd.read_csv(match_file)

    columns = ["ID", "onset_time", "offset_time", "spelled_pitch", "onset_velocity", 
        "offset_velocity", "channel", "match_status", "score_time", "score_dur", "voice", 
        "note_ID", "error_index", "skip_index"]

    with open(match_file, "r") as f:
        
        lines = f.readlines()
        match = [line.split() for line in lines if line[:2] != "//"]
        match = pd.DataFrame(match)
        match.columns = columns

        match.onset_time = match.onset_time.astype(float)
        match.offset_time = match.offset_time.astype(float)

        """TODO: check validity of the match"""

        """normalize score time by ticks per quarter note"""
        TPQN = int(re.search(r"\d+", lines[4]).group(0))
        match.score_time = match.score_time.astype(float) / TPQN
        match.score_dur = match.score_dur.astype(float) / TPQN	

        """parse measures from the note id information """
        match['measure'] = match['note_ID'].apply(get_measure)
    return match

def align_perf_score(perf, score, score_format="musicxml", use_matched=True):
    """using eita's alignment algorithm, save "_match.txt" files in dataset. Only run once
    perf: str without .mid extension, e.g "/import/c4dm-datasets/ATEPP/Sergei_Rachmaninoff/Etudes-Tableaux,_Op.39/No.6_in_A_Minor/00159"
    score: str without .mxl extension, e.g "/import/c4dm-datasets/ATEPP/Sergei_Rachmaninoff/Etudes-Tableaux,_Op.39/No.6_in_A_Minor/Rachmaninov_Etude-Tableau_op._39_no._6"
    output: 
    """
    if use_matched and os.path.exists(f"{perf}_match.txt"):
        print("done")
        return f"{perf}_match.txt"
    
    # alignment was attempted before but unsuccessfull. Skip this one
    if use_matched and os.path.exists(f"{perf}_spr.txt"):
        return 

    """escape parenthesis"""
    score = score.replace("(", "\(")
    score = score.replace(")", "\)")
    perf = perf.replace("(", "\(")
    perf = perf.replace(")", "\)")

    if score_format == "xml":
        os.system(f"./AlignmentTool_v190813/XMLToMIDIAlign.sh {score} {perf}")
    elif score_format == "musicxml":
        os.system(f"./AlignmentTool_v190813/MusicXMLToMIDIAlign.sh {score} {perf}")
    
    
    """remove the artifacts after matching"""
    # if os.path.exists(f"{perf}_spr.txt"): 
    #     os.system(f"rm {perf}_spr.txt")
    if os.path.exists(f"{perf}_corresp.txt"):
        os.system(f"rm {perf}_corresp.txt")
    if os.path.exists(f"{score}_spr.txt"): 
        os.system(f"rm {score}_spr.txt")
    if os.path.exists(f"{score}_hmm.txt"): 
        os.system(f"rm {score}_hmm.txt")
    if os.path.exists(f"{score}_fmt3x.txt"): 
        os.system(f"rm {score}_fmt3x.txt")


    return f"{perf}_match.txt"


def parse_score_markings(match, score):
    """parse the score using partitura package, link the score attributes with the note-match list """
    try:
        sc = pt.load_score_as_part(score)
    except:
        match['dynamics_marking'] = ""
        return match

    if not sc.dynamics:
        return match
    # append the dynamic markings to the score 
    TPQN = sc.dynamics[0].start.quarter
    dynamics = [(dyn.start.t / TPQN, dyn.end.t / TPQN, dyn.text) for dyn in sc.dynamics 
                    if (dyn.start and dyn.end and dyn.start.t < match.iloc[-1]['score_time'])]

    match['dynamics_marking'] = ""
    match_idx = 0
    for dm_start, dm_end, dm_text in dynamics: 
        while(match.iloc[match_idx]['score_time'] < dm_start): # move to the marking starting position
            match_idx += 1
        
        if dm_text in ["crescendo", "diminuendo"]:
            match.at[match_idx, 'dynamics_marking'] = dm_text + "_start"
            end_position = (match['score_time']-dm_end).abs().argsort()[0] # find the closest ending position
            match.at[end_position, 'dynamics_marking'] = dm_text + "_end"
        else:
            match.at[match_idx, 'dynamics_marking'] = dm_text

    return match

def update_match_with_score_features():
    all_match_files = glob.glob(f"{DATA_DIR}/**/*_match.txt", recursive=True)

    for idx, match_file in tqdm(enumerate(all_match_files)):
        match = parse_match(match_file)
        score_for_match = glob.glob(f"{match_file[:-15]}/*xml", recursive=True)
        updated_match = parse_score_markings(match, score_for_match[0])
        updated_match.to_csv(match_file[:-4] + ".csv")

    return 

def generate_alignments():
    """generate _match.txt files for each performance-score pair, under the same directory. """
    meta_csv = pd.read_csv(DATA_CSV)

    data_with_score = meta_csv[~meta_csv["score_path"].isna()]
    midi_list = data_with_score["midi_path"].tolist()
    score_list = data_with_score["score_path"].tolist()

    for perf, score in tqdm(zip(midi_list, score_list)):
        if "Rachmaninoff" not in perf:
            continue
        """remove extension"""
        perf = DATA_DIR + perf[:-4]
        score = DATA_DIR + ".".join(score.split(".")[:-1])

        if os.path.exists(score + ".mxl"):
            # unzip the mxl file
            score_dir = "/".join(score.split("/")[:-1])
            os.system(f"unzip -o {score}.mxl -d {score_dir}")

        if os.path.exists(score + ".musicxml"):
            align_perf_score(perf, score, score_format="musicxml")
        elif os.path.exists(score_dir + "/score.xml"):
            align_perf_score(perf, score_dir + "/score", score_format="xml")
        else:
            print("score doesn't exist! " + score)
            continue

def filter_unmatched():
    """filter out the pieces that"""
    meta_csv = pd.read_csv(DATA_CSV)

    data_with_score = meta_csv[~meta_csv["score_path"].isna()]
    midi_list = data_with_score["midi_path"].tolist()
    score_list = data_with_score["score_path"].tolist()

    # hook()
    mxl_count, mxl_unmatched_count = 0, 0
    musicxml_count, musicxml_unmatched_count = 0, 0
    for perf, score in tqdm(zip(midi_list, score_list)):
        perf = DATA_DIR + perf[:-4]
        score = DATA_DIR + ".".join(score.split(".")[:-1])

        if os.path.exists(score + ".mxl"):
            mxl_count += 1
            if (not os.path.exists(perf + "_match.txt")):
                mxl_unmatched_count += 1

        if os.path.exists(score + ".musicxml"):
            musicxml_count += 1
            if (not os.path.exists(perf + "_match.txt")):
                musicxml_unmatched_count += 1

    print(f"{mxl_unmatched_count}/{mxl_count}")
    print(f"{musicxml_unmatched_count}/{musicxml_count}")
    print(f"{(musicxml_unmatched_count+mxl_unmatched_count)}/{(mxl_count+musicxml_count)}")


def remove_all_matched():
    all_match_files = glob.glob(f"{DATA_DIR}/**/*_match.txt", recursive=True)
    for file in all_match_files:
        file = file.replace("(", "\(")
        file = file.replace(")", "\)")
        os.system(f"rm {file}")

    return 


def link_score_to_metadata():
    # add the newly added scores into the metadata csv
    meta_csv = pd.read_csv(DATA_CSV)
    chopin_scores = glob.glob(f"{DATA_DIR}/Frederic_Chopin/**/*xml") + glob.glob(f"{DATA_DIR}/Frederic_Chopin/**/*mxl")

    for score in chopin_scores:
        score_dir = "/".join(score.split("/")[4:-1])
        meta_csv.loc[meta_csv['midi_path'].str.contains(score_dir), 'score_path'] = "/".join(score.split("/")[4:])

    meta_csv.to_csv("ATEPP-metadata-1.2.csv")
    return 

if __name__ == "__main__":
    # remove_all_matched()
    # generate_alignments()
    # filter_unmatched()
    # link_score_to_metadata()

    # match = parse_match("../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No._17_in_B-Flat_Major,_K._570/I._Allegro/05511_match.txt")
    # parse_score_markings(match, "../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No._17_in_B-Flat_Major,_K._570/I._Allegro/score.xml")
    update_match_with_score_features()
    pass