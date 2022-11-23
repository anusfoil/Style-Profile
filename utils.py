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
    Note: the missing notes and extra notes are not included. 
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
        match.error_index = match.error_index.astype(int)

        """TODO: check validity of the match"""
        # large trunck of extra notes: might be repeat

        match = match[match['error_index'] == 0]

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
        print("used matched")
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
    if os.path.exists(f"{perf}_spr.txt"): 
        os.system(f"rm {perf}_spr.txt")
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
    match['dynamics_marking'] = ""
    try:
        sc = pt.load_score_as_part(score)
    except:
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


def calculate_tempo(match, level='ibi'):
    """plot tempo on beat or measure level"""
    match_beats = match[match['score_time'].apply(float.is_integer)]  # select the ones on the beat
    match_beats = match[match['error_index'] == 0] # not including extra notes 

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

    return match.round(6)

def update_match_with_score_features():
    """updated information: 
        ibi: inter-beat-interval, annotated for on-beat events. For other events  
        tempo: in beats-per-minute
        dynamics: marking on the event 

    """
    all_match_files = glob.glob(f"{DATA_DIR}/**/*_match.txt", recursive=True)

    for idx, match_file in tqdm(enumerate(all_match_files)):
        # if not "02195" in match_file:
        #     continue
        match = parse_match(match_file)
        score_for_match = glob.glob(f"{match_file[:-15]}/*xml", recursive=True)
        match_with_marking = parse_score_markings(match, score_for_match[0]) # dynamics 

        match_marking_tempo = calculate_tempo(match_with_marking) # ibi, imi and tempo

        match_marking_tempo.to_csv(match_file[:-4] + ".csv")

    return 

def generate_alignments():
    """generate _match.txt files for each performance-score pair, under the same directory. """
    meta_csv = pd.read_csv(DATA_CSV)

    data_with_score = meta_csv[~meta_csv["score_path"].isna()]
    midi_list = data_with_score["midi_path"].tolist()
    score_list = data_with_score["score_path"].tolist()

    for perf, score in tqdm(zip(midi_list, score_list)):
        if "24_Preludes,_Op._28" not in perf:
            continue
        """remove extension"""
        perf = DATA_DIR + perf[:-4]
        score = DATA_DIR + ".".join(score.split(".")[:-1])

        score_dir = "/".join(score.split("/")[:-1])
        if os.path.exists(score + ".mxl"):
            # unzip the mxl file
            os.system(f"unzip -o {score}.mxl -d {score_dir}")
            # hook()

        xml_dir = glob.glob(score_dir + "/*.xml")
        if os.path.exists(score + ".musicxml"):
            align_perf_score(perf, score, score_format="musicxml", use_matched=True)
        elif xml_dir:
            align_perf_score(perf, xml_dir[0][:-4], score_format="xml", use_matched=True)
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
    chopin_scores = glob.glob(f"{DATA_DIR}/Frederic_Chopin/**/*xml", recursive=True) + glob.glob(f"{DATA_DIR}/Frederic_Chopin/**/*mxl", recursive=True)

    for score in chopin_scores:
        if "24_Preludes,_Op._28" not in score:
            continue
        score_dir = "/".join(score.split("/")[4:-2]) + "/" + score.split("/")[-2][:7]
        meta_csv.loc[meta_csv['midi_path'].str.contains(score_dir), 'score_path'] = "/".join(score.split("/")[4:])

    meta_csv.to_csv("ATEPP-metadata-1.2.csv", index=False)
    return 


def match_preludes():
    meta_csv = pd.read_csv(DATA_CSV)
    meta_csv = meta_csv.drop(columns=["Unnamed: 0", "Unnamed: 0.1", "Unnamed: 0.1.1", "Unnamed: 0.1.1.1", "Unnamed: 0.1.1.1.1", "Unnamed: 0.1.1.1.1.1",
                                        "Unnamed: 0.1.1.1.1.1.1", "Unnamed: 0.1.1.1.1.1.1.1"])
    prelude_with_score = meta_csv[meta_csv["midi_path"].str.contains("ludes,_Op._28")]
    prelude_no_score = meta_csv[meta_csv["midi_path"].str.contains("Prelude,_Op._28")]

    paths = {
        "24": "No._24_in_D_Minor:_Allegro_appassionato",
        "22": "No._22_in_G_Minor:_Molto_agitato",
        "4": "No._4_in_E_Minor:_Largo",
        "15": "No._15_in_D-Flat_Major_Raindrop:_Sostenuto",
        "7": "No._7_in_A_Major:_Andantino",
        "11": "No._11_in_B_Major:_Vivace",
        "1": "No._1_in_C_Major:_Agitato",
        "16": "No._16_in_B-Flat_Minor:_Presto_con_fuoco",
        "3": "No._3_in_G_Major:_Vivace",
        "18": "No._18_in_F_Minor:_Molto_allegro",
        "10": "No._10_in_C-Sharp_Minor:_Molto_allegro",
        "14": "No._14_in_E-Flat_Minor:_Allegro",
        "2": "No._2_in_A_Minor:_Lento",
        "23": "No._23_in_F_Major:_Moderato",
        "21": "No._21_in_B-Flat_Major:_Cantabile",
        "6": "No._6_in_B_Minor:_Lento_assai",
        "8": "No._8_in_F-Sharp_Minor:_Molto_agitato",
        "19": "No._19_in_E-Flat_Major:_Vivace",
        "12": "No._12_in_G-Sharp_Minor:_Presto",
        "17": "No._17_in_A-Flat_Major:_Allegretto",
        "9": "No._9_in_E_Major:_Largo",
        "20": "No._20_in_C_Minor:_Largo",
        "5": "No._5_in_D_Major:_Molto_allegro",
        "13": "No._13_in_F-Sharp_Major:_Lento",
    }
    for i, row in prelude_no_score.iterrows():
        number = row['midi_path'].split("/")[-2].split("_")[1]
        if (prelude_with_score['track_duration'] == row['track_duration']).sum():
            meta_csv.drop(i)
        else:
            new_path = "Frederic_Chopin/24_Preludes,_Op._28/" + paths[number] + "/" + row["midi_path"].split("/")[-1]
            meta_csv.at[i, "midi_path"] = new_path
            os.rename(DATA_DIR + row['midi_path'], DATA_DIR + new_path)
    hook()

    meta_csv.to_csv("ATEPP-metadata-1.2.csv", index=False)
    return

if __name__ == "__main__":
    # remove_all_matched()
    # generate_alignments()
    # filter_unmatched()
    # link_score_to_metadata()
    # match_preludes()

    # match = parse_match("../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No._17_in_B-Flat_Major,_K._570/I._Allegro/05511_match.txt")
    # parse_score_markings(match, "../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No._17_in_B-Flat_Major,_K._570/I._Allegro/score.xml")
    update_match_with_score_features()
    pass