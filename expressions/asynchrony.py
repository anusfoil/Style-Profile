import numpy as np
import pretty_midi
import music21 as m21


def get_async_groups(match):
    """returns the chords or intervals that has the same metrical start time"""
    onset_groups = match.groupby(['score_time']).groups
    onset_groups = {k:v for k, v in onset_groups.items() if len(v) > 1}
    return onset_groups

def note_name_to_number(note_name):
    try: 
        return pretty_midi.note_name_to_number(note_name)
    except:
        note_name = note_name.replace("b", "-")
        p = m21.pitch.Pitch(note_name)
        return p.midi

def async_attributes(onset_groups, match, v=False):

    if not onset_groups:
        return {
        "sp_async_delta": np.nan,
        "sp_async_cor_onset": np.nan,
        "sp_async_cor_vel": np.nan,
        "sp_async_parts": np.nan
    }

    tol_delta, tol_cor, tol_cor_vel, tol_voice_std = 0, 0, 0, 0
    for _, indices in onset_groups.items():
        onset_times = match.loc[indices]['onset_time']
        delta = onset_times.max() - onset_times.min()
        if delta > 5: # some notes have the same score time because of repeat, but they are not actually from the same chord
            continue 
        tol_delta += delta 

        midi_pitch = match.loc[indices]['spelled_pitch'].apply(note_name_to_number)
        midi_pitch = midi_pitch - midi_pitch.min() # min-scaling
        onset_times = onset_times - onset_times.min()
        cor = np.corrcoef(midi_pitch, onset_times)[0, 1]
        tol_cor += (0 if np.isnan(cor) else cor)
    
        midi_vel = match.loc[indices]['onset_velocity'].astype(float)
        midi_vel = midi_vel - midi_vel.min()
        cor = np.corrcoef(midi_vel, onset_times)[0, 1]
        tol_cor_vel += (0 if np.isnan(cor) else cor)

        voices = match.loc[indices]['voice'].unique()
        voices_onsets = []
        for voice in voices:
            note_in_voice = match.loc[indices][match['voice'] == voice]
            voices_onsets.append(note_in_voice['onset_time'].mean())
        tol_voice_std += np.std(np.array(voices_onsets))
        

    return {
        "sp_async_delta": (tol_delta / len(onset_groups)),
        "sp_async_cor_onset": -(tol_cor / len(onset_groups)),
        "sp_async_cor_vel": -(tol_cor_vel / len(onset_groups)),
        "sp_async_voice_std": tol_voice_std / len(onset_groups)
    }
