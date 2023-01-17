import os, re, glob
import pandas as pd
from tqdm import tqdm
import numpy as np
import partitura as pt

import hook

###################################
### MATCH AND ALIGNMENTS
###################################

def get_measure(note_ID):
    note_info = note_ID.split("-")
    try:
        return int(note_info[1])
    except:
        return -1


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
    elif score_format == "mid":
        os.system(f"./AlignmentTool_v190813/MIDIToMIDIAlign.sh {score} {perf}")    
    
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

def generate_alignments():
    """generate _match.txt files for each performance-score pair, under the same directory. """
    meta_csv = pd.read_csv(DATA_CSV)

    data_with_score = meta_csv[~meta_csv["score_path"].isna()]
    midi_list = data_with_score["midi_path"].tolist()
    score_list = data_with_score["score_path"].tolist()

    for perf, score in tqdm(zip(midi_list, score_list)):
        if "K.333/3._Allegretto_grazioso" not in perf:
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

def dataframe_from_matchfile(match_path):
    """adapted from partitura package importmatch.py alignment_from_matchfile

    read .match file and returns a dataframe with note and snote information.
    """
    mf = pt.io.importmatch.MatchFile(match_path)

    result = []
    assert(mf.info()[-2].Attribute == "midiClockUnits")
    TPQN = mf.info()[-2].Value

    for line in mf.lines:
        if isinstance(line, pt.io.importmatch.MatchSnoteNote):
            result.append(
                dict(
                    ID=line.note.Number,
                    onset_time=round(line.note.Onset / TPQN, 3),
                    offset_time=round(line.note.Offset / TPQN, 3),
                    spelled_pitch=spelled_pitch,
                    onset_velocity=line.note.Velocity,
                    channel=line.note.Channel,
                    score_time=line.snote.OnsetInBeats,
                    score_dur=line.snote.DurationInBeats,
                    voice=0, # doesn't seems to find voice information
                )
            )
        elif isinstance(line, pt.io.importmatch.MatchSnoteNoteNew):
            modifier = "#" if line.snote.Modifier == 1 else ""
            if line.snote.Modifier == -1: modifier = "b" 
            spelled_pitch = f"{line.snote.NoteName}{modifier}{line.snote.Octave}"
            result.append(
                dict(
                    ID=line.note.Number,
                    onset_time=round(line.note.Onset / TPQN, 3),
                    offset_time=round(line.note.Offset / TPQN, 3),
                    spelled_pitch=spelled_pitch,
                    onset_velocity=line.note.Velocity,
                    channel=line.note.Channel,
                    score_time=line.snote.OnsetInBeats,
                    score_dur=line.snote.DurationInBeats,
                    voice=0, # doesn't seems to find voice information
                )
            )

        elif isinstance(line, pt.io.importmatch.MatchSnoteDeletion):
            if "leftOutTied" in line.snote.ScoreAttributesList:
                continue
            else:
                # result.append(dict(label="deletion", score_id=line.snote.Anchor))
                pass
        elif isinstance(line, pt.io.importmatch.MatchInsertionNote):
            # result.append(dict(label="insertion", performance_id=line.note.Number))
            pass
        elif isinstance(line, pt.io.importmatch.MatchOrnamentNote):
            if isinstance(line, pt.io.importmatch.MatchTrillNote):
                ornament_type = "trill"
            else:
                ornament_type = "generic_ornament"
            # result.append(
            #     dict(
            #         label="ornament",
            #         score_id=line.Anchor,
            #         performance_id=line.note.Number,
            #         type=ornament_type,
            #     )
            # )

    result = pd.DataFrame(result)
    return result


###################################
### SCORE FEATURES AND TEMPO
###################################

def find_note_from_match(note, match):

    TPQN = note.start.quarter
    """given a note object from partitura score, find the corresponding """
    note_pitch = "{}{}{}".format(note.step, note.alter_sign, note.octave)
    found_note = match[(match['score_time'] == (note.start.t / TPQN)) & (match['spelled_pitch'] == note_pitch)]

    return found_note

def get_score_offsets(match):
    if 'score_offset' not in match:
        match['score_offset'] = match['score_time'] + match['score_dur']
    return match

def parse_dynamic_markings(match, sc):

    if not sc.dynamics:
        return match
    # append the dynamic markings to the score 
    TPQN = sc.dynamics[0].start.quarter
    dynamics = [(dyn.start.t / TPQN, dyn.end.t / TPQN, dyn.text) for dyn in sc.dynamics 
                    if (dyn.start and dyn.end and (dyn.start.t / TPQN) < match.iloc[-1]['score_time'])]

    match_idx = 0
    for dm_start, dm_end, dm_text in dynamics: 
        while(match.iloc[match_idx]['score_time'] < dm_start): # move to the marking starting position
            match_idx += 1
        
        if dm_text in ["crescendo", "diminuendo"]:
            match.at[match_idx, 'dynamics_marking'] = dm_text + "_start"
            end_position = (match['score_time']-dm_end).abs().argsort().iloc[0] # find the closest ending position
            match.at[end_position, 'dynamics_marking'] = dm_text + "_end"
        else:
            match.at[match_idx, 'dynamics_marking'] = dm_text

    return match

def parse_articulation_markings(match, sc):
    legato_voice = []

    # add articulation to the match file
    for note in sc.notes:
        if note.articulations:
            found_note = find_note_from_match(note, match)
            if len(found_note):
                match.at[found_note.index, "articulation_marking"] = note.articulations[0]

        if note.voice in legato_voice: 
            found_note = find_note_from_match(note, match)
            if len(found_note):
                match.at[found_note.index, "articulation_marking"] = "legato"

        if note.slur_starts and (type(note) != pt.score.GraceNote): 
            legato_voice.append(note.voice) # the successive notes in the same voice are covered by legato slur.          
            found_note = find_note_from_match(note, match)
            if len(found_note):
                match.at[found_note.index, "articulation_marking"] = "legato"

        if note.slur_stops:
            # reminder: there might be case where the slur_starts show up after slur_stops. The case should be grace note
            if note.voice in legato_voice:
                legato_voice.remove(note.voice)

    return match

def parse_score_markings(match, score):
    """parse the score using partitura package, link the score attributes with the note-match list """

    if ('dynamics_marking' not in match) or ('articulation_marking' not in match):
        match['dynamics_marking'] = ""
        match['articulation_marking'] = ""
        try:
            sc = pt.load_score_as_part(score)
        except:
            return match

        match = parse_dynamic_markings(match, sc)
        match = parse_articulation_markings(match, sc)

    return match


def calculate_tempo(match):
    """returns tempo on event level
    NOTE: on the event level, there would be a lot of noise and fluctuations. 
    """

    if 'tempo' not in match:
        score_time_shift = np.concatenate((np.array([0.0]), match['score_time'][:-1].to_numpy()))
        score_time_diff = match['score_time'].to_numpy() - score_time_shift

        onset_time_shift = np.concatenate((np.array([0.0]), match['onset_time'][:-1].to_numpy()))
        onset_time_diff = match['onset_time'].to_numpy() - onset_time_shift

        match['ibi'] = onset_time_diff / score_time_diff
        match['ibi'].replace([np.inf, -np.inf], np.nan, inplace=True)
        match.loc[match['ibi'] < 0.1, 'ibi'] = np.nan # remove abnormal values 
        match['tempo'] = 60 / match['ibi'] 
        match['tempo'].replace([np.inf, -np.inf], np.nan, inplace=True)

    return match.round(6)



###################################
### DATA CLEANING AND STATISTICS
###################################


def data_stats():
    """compute the stats
        - pieces with xml score  
        - pieces aligned 
        - valid alignment
        - pieces with scores parsed by partitura 
        - pieces with dynamics 
    """
    meta_csv = pd.read_csv(DATA_CSV)

    data_with_score = meta_csv[~meta_csv["score_path"].isna()]
    midi_list = data_with_score["midi_path"].tolist()
    score_list = data_with_score["score_path"].tolist()

    # hook()
    data_aligend_count, aligned_valid_count, with_dynamics_count = 0, 0, 0
    for perf, score in tqdm(zip(midi_list, score_list)):
        perf = DATA_DIR + perf[:-4]
        score = DATA_DIR + ".".join(score.split(".")[:-1])


        if os.path.exists(perf + "_match.txt"):
            data_aligend_count += 1
            aligned_valid_count += (type(parse_match(perf + "_match.txt")) != None)
            
            match = parse_match(perf + "_match.csv")
            with_dynamics_count += ~match['dynamics_marking'].isna().all()
    
    print(f"Total data: {len(meta_csv)}")
    print(f"Data with score: {len(data_with_score)}")
    print(f"Data aligned: {data_aligend_count}")
    print(f"Data valid alignment: {aligned_valid_count}")
    print(f"Data with dynamics: {with_dynamics_count}")


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

def link_csv_to_metadata():
    # add the newly added scores into the metadata csv
    meta_csv = pd.read_csv(DATA_CSV)
    valid_match_csv = glob.glob(f"{DATA_DIR}/**/*_match.csv", recursive=True)

    for match_file in valid_match_csv:
        match_file_dir = match_file[22:-10]
        meta_csv.at[meta_csv['midi_path'].str.contains(match_file_dir), 'valid_match'] = "/".join(match_file.split("/")[3:])

    meta_csv.to_csv("ATEPP-metadata-1.3.csv", index=False)

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


def update_asap_performer():
    asap_metadata = pd.read_csv("../Datasets/asap-dataset/metadata.csv")
    asap_maestro = asap_metadata[~asap_metadata['maestro_midi_performance'].isna()]

    year = asap_maestro['maestro_midi_performance'].str[10:14]
    id = asap_maestro['midi_performance'].str.split("/").str[-1]
    id = id.str.split(r"\d", expand=True)[0]

    asap_maestro["performer"] = year + id

    asap_nonmaestro = asap_metadata[asap_metadata['maestro_midi_performance'].isna()]
    nonmaestro_id = asap_nonmaestro['midi_performance'].str.split("/").str[-1].str.split(r"\d", expand=True)[0]
    uniqueid = pd.Series(asap_maestro["performer"].unique())
    nonmaestro_unique = nonmaestro_id.apply(lambda x: len(uniqueid[uniqueid.str.contains(x + r"$")]) == 1)
    
    nonmaestro_matched = asap_nonmaestro[nonmaestro_unique]
    nonmaestro_id_matched = nonmaestro_id[nonmaestro_unique]
    nonmaestro_matched['performer'] = nonmaestro_id_matched.apply(lambda x: uniqueid[uniqueid.str.contains(x + r"$")].iloc[0])

    asap_metadata = pd.concat([asap_maestro, nonmaestro_matched])
    asap_metadata.to_csv("../Datasets/asap-dataset/metadata-v1.0.csv", index=False)
    
    return 


if __name__ == "__main__":
    # remove_all_matched()
    # generate_alignments()
    # match_preludes()

    # match = parse_match("../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No._17_in_B-Flat_Major,_K._570/I._Allegro/05512_match.csv")
    # match = parse_match('../Datasets/ATEPP-1.1//Franz_Schubert/Piano_Sonata_No.13_in_A,_D.664/3._Allegro/03975_match.csv')
    # parse_score_markings(match, "../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No._17_in_B-Flat_Major,_K._570/I._Allegro/score.xml")
    # update_match_with_score_features()
    # data_stats()
    update_asap_performer()
    
    pass