from midi_classification import midi_classification
import pretty_midi
from collections import Counter
import os

class midi_trainer:

    #this function identifies the melody track (lowest polyphony, highest variety),
    #and returns only the ordered list of pitches.
    def extract_note_sequence(filepath):
        try:
            midi_data = pretty_midi.PrettyMIDI(filepath)
        except Exception as e:
            print(f"Error loading MIDI file '{filepath}': {e}")
            return []

        best_track = None
        best_score = -1

        # Iterate through every non-drum track in the file
        for instrument in midi_data.instruments:

            if instrument.is_drum:
                continue

            notes = instrument.notes

            #extremely small tracks provide no usable melody info
            if len(notes) < 12:
                continue


            #count how many notes overlap in time indicator of chords.
            #MUSIC THEORY LESSON TIME (you might know this):
            #a chord is multiple notes (3 or more) played at the same time to create a harmony
            overlaps = 0
            for i in range(1, len(notes)):
                if notes[i].start < notes[i-1].end:
                    overlaps += 1

            #number of unique pitches vs total pitches
            unique_pitches = len(set(n.pitch for n in notes))
            total_pitches = len(notes)

            unique_ratio = unique_pitches / total_pitches
            polyphony_ratio = overlaps / total_pitches


            score = unique_ratio - polyphony_ratio

            #keep the best candidate
            if score > best_score:
                best_score = score
                best_track = notes

        if not best_track:
            return []

        #convert pretty_midi Note objects integer pitch list
        return [n.pitch for n in best_track]

    #this function trains the agent using probability distributions that were learned from the training midi files
    #basically applies Bayes Theorem to compute probabilities
    def train_interval_model_from_folder(
            folder_path,
            max_files=None,
    ):
        clamp_interval = 12
        weight = 1.0

        # Instead of grouping by major/minor, we now group EXACTLY by key name
        # (e.g., "C-minor", "E-minor", "F#-major"), matching the classifier.
        interval_counts_per_key = {}

        num_files = 0

        for filename in os.listdir(folder_path):
            if not filename.lower().endswith((".mid", ".midi")):
                continue

            filepath = os.path.join(folder_path, filename)
            num_files += 1

            if max_files is not None and num_files > max_files:
                break

            pitches = midi_trainer.extract_note_sequence(filepath)
            if len(pitches) < 2:
                continue

            #classify the key of the training file
            key_info = midi_classification.classify_key(pitches)
            key_name = key_info["key"]

            #only keep keys recognized by our new fixed key dictionaries
            if key_name not in midi_classification.MAJOR_KEYS and \
                    key_name not in midi_classification.MINOR_KEYS:
                print("  ⚠ Ignoring unrecognized key:", key_name)
                continue

            #create a new interval counter for this key if needed
            if key_name not in interval_counts_per_key:
                interval_counts_per_key[key_name] = Counter()

            #extract difference between consecutive notes (intervals)
            for i in range(len(pitches) - 1):
                interval = pitches[i + 1] - pitches[i]

                #ignore weird intervals
                if not isinstance(interval, int):
                    continue
                if abs(interval) > clamp_interval:
                    continue

                interval_counts_per_key[key_name][interval] += 1

        #edge case
        if not interval_counts_per_key:
            print("No intervals found in training data.")
            return {}

        interval_probs_per_key = {}

        for key_name, counter in interval_counts_per_key.items():

            if not counter:
                continue

            intervals = sorted(counter.keys())
            K = len(intervals)
            total = sum(counter.values())

            interval_probs = {}

            for interval in intervals:
                count = counter[interval]
                prob = (count + weight) / (total + weight * K)

                interval_probs[interval] = prob

            #store probability distribution for this key
            interval_probs_per_key[key_name] = interval_probs

        print(f"Trained on {num_files} MIDI files.")
        print(f"Learned {len(interval_probs_per_key)} key-specific models.")

        return interval_probs_per_key
