import os
import pretty_midi
from midi_classification import midi_classification
from midi_enhancement import midi_enhancement
from midi_trainer import midi_trainer


#this helper just gives every file a unique name so nothing gets overwritten
def get_unique_filename(base_name, extension=".mid"):
    i = 1
    while True:
        filename = f"{base_name}{i}{extension}"
        if not os.path.exists(filename):
            return filename
        i += 1


def run(
        input_midi,
        training_folder="training_midis",
        insert_prob=0.35
):

    #treat input like a list so we can loop through it easily
    if not isinstance(input_midi, list):
        input_files = [input_midi]
    else:
        input_files = input_midi

    #process each MIDI file
    for input_file in input_files:


        #quick sanity check
        if not os.path.isfile(input_file):
            print(f"Error: Input MIDI '{input_file}' not found.")
            continue

        print(f"\nLoading input MIDI: {input_file}")
        notes = midi_classification.load_midi_file(input_file)
        if not notes:
            print("No valid notes found.")
            continue


        print("\nClassifying key...")
        classified = midi_classification.classify_key(notes)
        key_name = classified["key"]
        relative_key = classified["relative_key"]

        print(f"Detected key: {key_name}")
        print(f"Relative key: {relative_key}")


        print("\nAutocorrecting out-of-key notes...")

        #first check if the input melody actually *needs* correction
        scale = {**midi_classification.MAJOR_KEYS, **midi_classification.MINOR_KEYS}[key_name]

        needs_correction = False
        for n in notes:
            if (n % 12) not in scale:
                needs_correction = True
                break

        #if melody is perfectly in-key skip correction step entirely
        if not needs_correction:
            print("All notes already in key! Good Job!")
            corrected_notes = notes[:]   #just keep original notes
            midi_data = pretty_midi.PrettyMIDI(input_file)

        else:
            #actually run the correction
            corrected_notes = midi_enhancement.correct_notes_to_key(notes, key_name)

            #reload full midi so we can apply pitch changes WITH timing
            midi_data = pretty_midi.PrettyMIDI(input_file)
            p_index = 0

            for inst in midi_data.instruments:
                if inst.is_drum:
                    continue
                for n in inst.notes:
                    if p_index < len(corrected_notes):
                        n.pitch = corrected_notes[p_index]
                    p_index += 1

            #save corrected version next to original name
            input_base = os.path.splitext(os.path.basename(input_file))[0]
            corrected_base = f"{input_base}_corrected"
            corrected_output = get_unique_filename(corrected_base)

            midi_data.write(corrected_output)
            print(f"Saved corrected file as: {corrected_output}")



        print("\nTraining interval model...")
        interval_probs = midi_trainer.train_interval_model_from_folder(training_folder)

        #try to use the model that matches our detected key
        interval_probs_for_key = interval_probs.get(key_name, None)
        if interval_probs_for_key is None:
            print(f"No interval model found for key {key_name}")
            interval_probs_for_key = next(iter(interval_probs.values()))


        #enhance melodies using probabilities from training set
        print("\nEnhancing melody...")

        enhanced_events = midi_enhancement.enhance_melody_with_intervals_and_rhythm(
            midi_data,
            key_name,
            interval_probs_for_key,
            insert_prob=insert_prob
        )


        #save enhanced version
        input_base = os.path.splitext(os.path.basename(input_file))[0]
        enhanced_base = f"{input_base}_enhanced"
        enhanced_output = get_unique_filename(enhanced_base)

        midi_enhancement.save_rhythmic_midi(
            input_file,
            enhanced_events,
            enhanced_output
        )

        #some quick debugging info
        print("-ORIGINAL NOTE COUNT:", len(notes))
        print("-CORRECTED NOTE COUNT:", len(corrected_notes))
        print("-ENHANCED NOTE COUNT:", len(enhanced_events))
        print(f"Saved enhanced file as: {enhanced_output}")



# if __name__ == "__main__":
#     run(
#         input_midi="c-minor.mid",
#         training_folder="training_midis",
#         insert_prob=0.5
#
#     )

# if __name__ == "__main__":
#     run(
#         input_midi="d#minor.mid",
#         training_folder="training_midis",
#         insert_prob=0.5
#     )

if __name__ == "__main__":
    run(
        input_midi="cminor_outofkey.mid",
        training_folder="training_midis",
        insert_prob=0.5
    )
