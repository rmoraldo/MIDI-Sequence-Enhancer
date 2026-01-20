import pretty_midi

# this class is used to classify an input midi file into a musical key
class midi_classification:
    # All the major and minor keys, stored in a dictionary that holds the notes of each key
    # C = 0, C# = 1, D = 2, D# = 3, E = 4, F = 5, F# = 6, G = 7, G# = 8, A = 9, A# = 10, B = 11
    #
    # *** As requested: SHARPS ONLY, no enharmonic keys like Cb, Db/Eb hybrids, etc. ***

    MAJOR_KEYS = {
        "C-major":   [0, 2, 4, 5, 7, 9, 11],
        "C#-major":  [1, 3, 5, 6, 8, 10, 0],
        "D-major":   [2, 4, 6, 7, 9, 11, 1],
        "D#-major":  [3, 5, 7, 8, 10, 0, 2],
        "E-major":   [4, 6, 8, 9, 11, 1, 3],
        "F-major":   [5, 7, 9, 10, 0, 2, 4],
        "F#-major":  [6, 8, 10, 11, 1, 3, 5],
        "G-major":   [7, 9, 11, 0, 2, 4, 6],
        "G#-major":  [8, 10, 0, 1, 3, 5, 7],
        "A-major":   [9, 11, 1, 2, 4, 6, 8],
        "A#-major":  [10, 0, 2, 3, 5, 7, 9],
        "B-major":   [11, 1, 3, 4, 6, 8, 10]
    }

    MINOR_KEYS = {
        "C-minor":   [0, 2, 3, 5, 7, 8, 10],
        "C#-minor":  [1, 3, 4, 6, 8, 9, 11],
        "D-minor":   [2, 4, 5, 7, 9, 10, 0],
        "D#-minor":  [3, 5, 6, 8, 10, 11, 1],
        "E-minor":   [4, 6, 7, 9, 11, 0, 2],
        "F-minor":   [5, 7, 8, 10, 0, 1, 3],
        "F#-minor":  [6, 8, 9, 11, 1, 2, 4],
        "G-minor":   [7, 9, 10, 0, 2, 3, 5],
        "G#-minor":  [8, 10, 11, 1, 3, 4, 6],
        "A-minor":   [9, 11, 0, 2, 4, 5, 7],
        "A#-minor":  [10, 0, 1, 3, 5, 6, 8],
        "B-minor":   [11, 1, 2, 4, 6, 7, 9]
    }

    # IF YOU SEE THIS HERE IS A FREE MUSIC THEORY LESSON :)
    # each minor key has a major counterpart (called relative keys i.e C-minor has the same keys as Eb major)
    # this dictionary stores the relative keys for each key
    RELATIVE_KEYS = {
        "C-major":   "A-minor",
        "C#-major":  "A#-minor",
        "D-major":   "B-minor",
        "D#-major":  "C-minor",
        "E-major":   "C#-minor",
        "F-major":   "D-minor",
        "F#-major":  "D#-minor",
        "G-major":   "E-minor",
        "G#-major":  "F-minor",
        "A-major":   "F#-minor",
        "A#-major":  "G-minor",
        "B-major":   "G#-minor",

        "A-minor":   "C-major",
        "A#-minor":  "C#-major",
        "B-minor":   "D-major",
        "C-minor":   "D#-major",
        "C#-minor":  "E-major",
        "D-minor":   "F-major",
        "D#-minor":  "F#-major",
        "E-minor":   "G-major",
        "F-minor":   "G#-major",
        "F#-minor":  "A-major",
        "G-minor":   "A#-major",
        "G#-minor":  "B-major"
    }

    # This function loads a midi file and stores the notes in a list
    def load_midi_file(filepath):
        try:
            midi_data = pretty_midi.PrettyMIDI(filepath)
        except Exception as e:
            print(f"Error loading midi file: {e}")
            return []

        # get the midi notes and put them into a list
        notes = []
        for instrument in midi_data.instruments:
            if instrument.is_drum:
                continue
            for note in instrument.notes:
                notes.append(note.pitch)

        return notes

    # this function classifies a series of notes into a musical key
    def classify_key(notes):
        if not notes:
            return {"key": "Unknown", "relative_key": None}

        notes_mod12 = [n % 12 for n in notes]
        all_keys = {**midi_classification.MAJOR_KEYS, **midi_classification.MINOR_KEYS}

        best_key = None
        best_score = -1

        for key_name, key_notes in all_keys.items():
            score = sum((n in key_notes) for n in notes_mod12)

            if score > best_score:
                best_score = score
                best_key = key_name
            elif score == best_score and "minor" in key_name and "minor" not in best_key:
                # prefer minor key on ties
                best_key = key_name

        relative = midi_classification.RELATIVE_KEYS.get(best_key, None)
        return {"key": best_key, "relative_key": relative}
