import os, sys, glob, hook, time
import warnings
sys.path.insert(0, "../partitura")
sys.path.insert(0, "../")
from tests import test_performance_codec
import partitura as pt
import parangonar as pa
import matplotlib.pyplot as plt
from collections import defaultdict
import pandas as pd
import numpy as np
from tqdm import tqdm
import numpy.lib.recfunctions as rfn
from matplotlib.ticker import PercentFormatter


VIENNA_MATCH_DIR = "../Datasets/vienna4x22/match/"
VIENNA_MUSICXML_DIR = "../Datasets/vienna4x22/musicxml/"
VIENNA_PERFORMANCE_DIR = "../Datasets/vienna4x22/midi/"

ASAP_DIR = "../Datasets/asap-dataset-alignment/"
ASAP_MATCH = "../Datasets/asap-dataset-alignment/Scriabin/Sonatas/5/Yeletskiy07M_note_alignments/note_alignment.tsv"
ASAP_MUSICXML = "../Datasets/asap-dataset-alignment/Scriabin/Sonatas/5/xml_score.musicxml"
ASAP_PERFORMANCE = "../Datasets/asap-dataset-alignment/Scriabin/Sonatas/5/Yeletskiy07M.mid"

BMZ_MATCH_DIR = "../Datasets/pianodata-master/match"
BMZ_MUSICXML_DIR = "../Datasets/pianodata-master/xml/"

ATEPP_DIR = "../Datasets/ATEPP-1.1"
ATEPP_META_DIR = "../Datasets/ATEPP-1.1/ATEPP-metadata-1.3.csv"


def load_dataset_pf(datasets=['ASAP'], return_metadata=False):
    """load the performance features for the given dataset from the saved
    .npy arrays. Return list of numpy arrays.

    Args:
        dataset (str): dataset to process. Defaults to 'ASAP'.
        return_metadata (bool): return a dict with the list of composer and performer of the features. optional.  
    """

    pf_paths = []
    meta_dict = defaultdict(list)
    for dataset in datasets:
        if dataset == "VIENNA422":
            pf_paths.extend(glob.glob(os.path.join(VIENNA_MATCH_DIR, "*.npy")))
            meta_dict["composer"].extend([path.split("/")[4].split("_")[0] for path in pf_paths])
            meta_dict["performer"].extend([path.split("/")[4].split("_")[-3] for path in pf_paths])

        if dataset == "ASAP":
            pf_paths.extend(glob.glob(os.path.join(ASAP_DIR, "**/*.npy"), recursive=True))
            meta_dict["composer"].extend([path.split("/")[3] for path in pf_paths])
            meta_dict["performer"].extend([path.split("/")[-1].split("_")[0] for path in pf_paths])

        if dataset == "ATEPP":
            pf_paths.extend(glob.glob(os.path.join(ATEPP_DIR, "**/*.npy"), recursive=True))
            meta_csv = pd.read_csv(ATEPP_META_DIR)
            meta_dict["performer"].extend([meta_csv[meta_csv['midi_path'].str.contains(
                                            path.split("/")[-1][:5])]['artist'] for path in pf_paths])
            meta_dict['performer'] = [info.item() if len(info) == 1 else "unfound" for info in meta_dict['performer'] ]
            meta_dict["composer"].extend( [path.split("/")[3] for path in pf_paths])
        if dataset == "BMZ":
            pf_paths.extend(glob.glob(os.path.join(BMZ_MATCH_DIR, "**/*.npy"), recursive=True))
            composer = [path.split("/")[-1].split("_")[0] for path in pf_paths]
            meta_dict["composer"].extend(composer)
            # TODO: change this
            meta_dict["performer"].extend(["Magdaloff" if c == "chopin" else "Zeillinger" for c in composer])

    pf = [np.load(path, allow_pickle=True) for path in pf_paths]
    if return_metadata:
        return pf, meta_dict
    
    return pf



def atepp_alignment():
    """redo the alignment of ATEPP dataset using parangonar"""

    score_paths, performance_paths = [], []
    all_performances = glob.glob(os.path.join(ATEPP_DIR, "**/*[0-9].mid"), recursive=True)
    for pp in all_performances:
        route = "/".join(pp.split("/")[:-1]) + "/"
        sp = glob.glob(route + "*.mxl") + glob.glob(route + "*.musicxml") 
        if len(sp):
            score_paths.append(sp[0])
            performance_paths.append(pp)

    for sp, pp in tqdm(zip(score_paths[2142:], performance_paths[2142:])):

        if sp == '../Datasets/ATEPP-1.1/Robert_Schumann/Kreisleriana,_Op._16/VIII._Schnell_und_spielend/musicxml_cleaned.musicxml':
            continue

        score = pt.load_score(filename= sp)
        performance = pt.load_performance_midi(filename=pp)

        # compute note arrays from the loaded score and performance
        pna = performance.note_array()
        sna = score.note_array(include_grace_notes=True)

        # match the notes in the note arrays
        sdm = pa.DualDTWNoteMatcher()
        pred_alignment = sdm(sna, pna)

        outdir = pp[:-4]
        os.makedirs(outdir, exist_ok=True)
        pa.match.save_parangonada_csv(pred_alignment, performance, score, outdir=outdir)

    return pred_alignment

def atepp_alignment_stats():
    parangonar_alignment_paths = glob.glob(os.path.join(ATEPP_DIR, "**/[!z]*n.csv"), recursive=True)

    p_total_match, p_total_insertion, p_total_deletion = 0, 0, 0
    p_match_percent = []
    for alignment_path in tqdm(parangonar_alignment_paths):
        alignment = pt.io.importparangonada.load_parangonada_alignment(alignment_path)
        match_aligns = [a for a in alignment if a['label'] == 'match']
        insertion_aligns = [a for a in alignment if a['label'] == 'insertion']
        deletion_aligns = [a for a in alignment if a['label'] == 'deletion']
        p_total_match += len(match_aligns)
        p_total_insertion += len(insertion_aligns)
        p_total_deletion += len(deletion_aligns)
        p_match_percent.append(len(match_aligns) / (len(insertion_aligns) + len(deletion_aligns) + len(match_aligns)))
        # print(f"match: {len(match_aligns)}; insertion: {len(insertion_aligns)}; deletion: {len(deletion_aligns)}")

    n_total_match, n_total_match_error, n_total_insertion, n_total_deletion = 0, 0, 0, 0
    n_match_percent = []
    nakamura_alignment_paths = glob.glob(os.path.join(ATEPP_DIR, "**/*_match.txt"), recursive=True)
    for alignment_path in tqdm(nakamura_alignment_paths):
        _, _, alignment, m_score = pt.load_nakamuramatch(alignment_path)
        match_aligns = m_score[m_score['errorindex'] == 0]
        match_align_error_pitch = m_score[m_score['errorindex'] == 1]
        insertion_aligns = [a for a in alignment if a['label'] == 'insertion']
        deletion_aligns = [a for a in alignment if a['label'] == 'deletion']
        n_total_match += len(match_aligns)
        n_total_match_error += len(match_align_error_pitch)
        n_total_insertion += len(insertion_aligns)
        n_total_deletion += len(deletion_aligns)
        n_match_percent.append(len(match_aligns) / (len(insertion_aligns) + len(deletion_aligns) + len(match_aligns) + len(match_align_error_pitch)))


    fig, (ax1, ax2) = plt.subplots(1, 2)
    # ax1.pie([p_total_match, p_total_insertion, p_total_deletion], \
    #         labels=["match", "insertion", "deletion"], autopct='%1.1f%%')

    # ax2.pie([n_total_match, n_total_match_error, n_total_insertion, n_total_deletion], \
    #         labels=["match", "match_error", "insertion", "deletion"], autopct='%1.1f%%')
    
    ax1.hist(p_match_percent, bins=20, edgecolor = "black", weights=np.ones(len(p_match_percent)) / len(p_match_percent))
    ax2.hist(n_match_percent, bins=20, edgecolor = "black", weights=np.ones(len(n_match_percent)) / len(n_match_percent))

    plt.title("distribution of files with match note percent (parangonar vs. nakamura)")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
    plt.show()

    return 


def process_dataset_pf(datasets=['ASAP'], only_return_paths=False):
    """process the performance features for the given dataset. Save the 
    computed features in the form of numpy arrays in the same directory as 
    performance data.

    Args:
        datasets (list): dataset to process. Defaults to ['ASAP'].
    """

    for dataset in datasets:
        if "VIENNA422" in dataset:
            performance_paths = glob.glob(os.path.join(VIENNA_PERFORMANCE_DIR, "*[!e].mid"))
            alignment_paths = [(VIENNA_MATCH_DIR + pp.split("/")[-1][:-4] + ".match") for pp in performance_paths]
            score_paths = [(VIENNA_MUSICXML_DIR + pp.split("/")[-1][:-8] + ".musicxml") for pp in performance_paths]
            performance_paths = [None] * len(alignment_paths) # don't use the given performance, use the aligned.
        if "ASAP" in dataset:
            performance_paths = glob.glob(os.path.join(ASAP_DIR, "**/*[!e].mid"), recursive=True)
            alignment_paths = [(pp[:-4] + "_note_alignments/note_alignment.tsv") for pp in performance_paths][325:]
            score_paths = [os.path.join("/".join(pp.split("/")[:-1]), "xml_score.musicxml") for pp in performance_paths]
        if "ATEPP" in dataset:
            alignment_paths = glob.glob(os.path.join(ATEPP_DIR, "**/[!z]*n.csv"), recursive=True)
            performance_paths = [(aa[:-10] + ".mid") for aa in alignment_paths]
            score_paths = [glob.glob(os.path.join("/".join(pp.split("/")[:-1]), "*.*l"))[0] for idx, pp in enumerate(performance_paths)]
        if "BMZ" in dataset:
            alignment_paths = glob.glob(os.path.join(BMZ_MATCH_DIR, "**/*.match"), recursive=True)
            alignment_paths = [p for p in alignment_paths if (("Take" not in p))][173:]
            score_paths = [BMZ_MUSICXML_DIR + ap.split("/")[-1][:-6] + ".xml" for ap in alignment_paths]
            score_paths = [sp[:-4] + ".musicxml" if "mozart" in sp else sp for sp in score_paths]
            performance_paths = [None] * len(alignment_paths) # don't use the given performance, use the aligned.
        
        if only_return_paths:
            return alignment_paths, score_paths, performance_paths

        prev_s_path = None
        for s_path, p_path, a_path in tqdm(zip(score_paths, performance_paths, alignment_paths)):

            # parsing error
            if s_path == '../Datasets/ATEPP-1.1/Frederic_Chopin/Scherzo_No._4_in_E_Major,_Op._54,_B._148/score.xml':
                continue
            if s_path == '../Datasets/ATEPP-1.1/Frederic_Chopin/Nocturne_No.13_in_C_minor,_Op._48_No._1/score.xml':
                continue
            if s_path == '../Datasets/ATEPP-1.1/Frederic_Chopin/24_Preludes,_Op._28/No._7_in_A_Major:_Andantino/score.xml':
                continue
            if s_path == '../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No.4_in_E_flat,_K.282/2._Menuetto_I-II/score.xml':
                continue
            if s_path == "../Datasets/pianodata-master/xml/chopin_op35_Mv3.xml": # BMZ
                continue
            if s_path == '../Datasets/asap-dataset-alignment/Chopin/Scherzos/31/xml_score.musicxml': # ASAP
                continue
            if s_path == '../Datasets/asap-dataset-alignment/Ravel/Gaspard_de_la_Nuit/1_Ondine/xml_score.musicxml': # ASAP
                continue
            if a_path == '../Datasets/asap-dataset-alignment/Beethoven/Piano_Sonatas/23-1/LiuC02M_note_alignments/note_alignment.tsv':
                continue # tempo_grad floating point error
            if s_path == '../Datasets/asap-dataset-alignment/Scriabin/Sonatas/5/xml_score.musicxml': # ASAP tempo
                continue
            if s_path == '../Datasets/ATEPP-1.1/Frederic_Chopin/Scherzo_No._4_in_E_Major,_Op._54,_B._148/Scherzo_No.4_F.Chopin_Op.54.mxl':
                continue
            if s_path == '../Datasets/ATEPP-1.1/Frederic_Chopin/Impromptu_No._2_in_F-Sharp_Major,_Op._36/Frdric_Chopin_Impromptu_No._2_in_F-sharp_major_Op._36.mxl':
                continue
            if s_path == '../Datasets/ATEPP-1.1/Frederic_Chopin/24_Preludes,_Op._28/No._7_in_A_Major:_Andantino/Prlude_Opus_28_No._7_in_A_Major.mxl':
                continue
            # if s_path == '../Datasets/ATEPP-1.1/Alexander_Scriabin/Piano_Sonata_No._5,_Op._53/musicxml_cleaned.musicxml':
            #     continue

            # ATEPP: skip the recently computed ones and the bad ones from alignment
            if dataset == 'ATEPP':
                
                # file_path = f"{a_path[:-4]}_perf_features.npy"
                # if (os.path.exists(file_path) and "Aug" in time.ctime(os.path.getmtime(file_path))):
                #     continue
            
                alignment = pt.io.importparangonada.load_parangonada_alignment(a_path)
                match_aligns = [a for a in alignment if a['label'] == 'match']
                insertion_aligns = [a for a in alignment if a['label'] == 'insertion']
                deletion_aligns = [a for a in alignment if a['label'] == 'deletion']
                if (len(match_aligns) / (len(insertion_aligns) + len(deletion_aligns) + len(match_aligns))) < 0.5:
                    continue

            if (os.path.exists(s_path) and os.path.exists(a_path)):

                if prev_s_path == s_path:
                    pf, score = compute_performance_features(s_path, a_path, p_path, score=score, append_pe=True)
                else:
                    pf, score = compute_performance_features(s_path, a_path, p_path, append_pe=True)

                if dataset == "ASAP":
                    np.save(f"{p_path[:-4]}_perf_features.npy", pf)
                if (dataset == "BMZ") or (dataset == "VIENNA422"):
                    np.save(f"{a_path[:-6]}_perf_features.npy", pf) 
                if (dataset == "ATEPP"):
                    np.save(f"{a_path[:-4]}_perf_features.npy", pf)                 
                prev_s_path = s_path
            else:
                print(f"Data incomplete for {a_path}")

    return 


def compute_performance_features(score_path, alignment_path, performance_path=None, score=None, append_pe=False):
    """compute the performance feature given score, alignment and performance path.

    Args:
        dataset (str, optional): _description_. Defaults to 'ASAP'.
    """

    if not isinstance(performance_path, type(None)): # use the performance if it's given
        performance = pt.load_performance(performance_path)

    if alignment_path[-5:] == "match":
        performance, alignment = pt.load_match(alignment_path)
    elif alignment_path[-3:] == "tsv":
        alignment = pt.io.importparangonada.load_alignment_from_ASAP(alignment_path)
    elif alignment_path[-3:] == "csv": # case for ATEPP
        alignment = pt.io.importparangonada.load_parangonada_alignment(alignment_path)

    if isinstance(score, type(None)): # if no loaded score from previous round
        score = pt.load_musicxml(score_path)
        if alignment_path[-3:] == "csv": # case for ATEPP
            score = pt.load_musicxml(score_path, force_note_ids='keep')
            # if ("_" in alignment[0]['score_id']):
            #     score = pt.score.unfold_part_maximal(pt.score.merge_parts(score.parts)) 
        # if doesn't match the version in alignment, unfold the score.
        # if ('score_id' in alignment[0]) and ("-" in alignment[0]['score_id']) and ("-" not in score.note_array()['id'][0]): 
        #     score = pt.score.unfold_part_maximal(pt.score.merge_parts(score.parts)) 
    
    # for a in alignment:
    #     if 'score_id' in a and  "-" in a['score_id']:
    #         a['score_id'] = a['score_id'][:-2]

    pf, res = pt.musicanalysis.compute_performance_features(score, performance, alignment, 
                                                            feature_functions="all")

    # append the performance encodings to the pf 
    if append_pe:
        parameters, snote_ids = pt.musicanalysis.encode_performance(score, performance, alignment)
        pf = rfn.merge_arrays([pf, parameters], flatten=True)
    return pf, score


def get_atepp_overlap(): 
    # get the atepp subset with pieces of more than 8+ performances
    atepp_meta = pd.read_csv(ATEPP_META_DIR)
    score_groups = atepp_meta.groupby(['score_path']).count().sort_values(['midi_path'], ascending=False)
    selected_scores = score_groups.iloc[4:280]
    hook()
    return 


if __name__ == "__main__":


    get_atepp_overlap()
    # atepp_alignment()
    # atepp_alignment_stats()
    process_dataset_pf(datasets=[
                                # "BMZ",
                                # "VIENNA422",
                                # "ASAP",
                                "ATEPP",
                                ])
    
    # load_dataset_pf(datasets=[
    #                         # "BMZ",
    #                         # "VIENNA422",
    #                         "ASAP",
    #                         # "ATEPP",
    #                         ])
