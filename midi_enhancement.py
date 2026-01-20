from midi_classification import midi_classification
import pretty_midi
import random

class midi_enhancement:

    #this function corrects any notes that are out of key (same as before)
    def correct_notes_to_key(notes, key_name):
        if not notes:
            return []

        all_keys = {**midi_classification.MAJOR_KEYS, **midi_classification.MINOR_KEYS}
        if key_name not in all_keys:
            raise ValueError(f"Unknown key: {key_name}")

        scale = all_keys[key_name]
        corrected = []

        for n in notes:
            pc = n % 12

            #if note is already in the key, keep it
            if pc in scale:
                corrected.append(n)
                continue

            #otherwise move note to the closest pitch class in the key
            best_delta = None
            best_dist = None

            for target_pc in scale:
                raw = (target_pc - pc) % 12

                #make sure the note moves in the closest direction (music is circular)
                if raw > 6:
                    raw -= 12

                dist = abs(raw)
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_delta = raw

            corrected.append(n + best_delta)

        return corrected

    #this function writes a MIDI file using custom rhythmic note events
    def save_rhythmic_midi(template_filepath, note_events, output_filepath):
        try:
            midi = pretty_midi.PrettyMIDI(template_filepath)
        except Exception as e:
            print("Error loading template:", e)
            return

        #find the *first* non-drum track (this is usually the melody)
        melody_inst = None
        for inst in midi.instruments:
            if not inst.is_drum:
                melody_inst = inst
                break

        if melody_inst is None:
            print("No melodic track found in MIDI (only drums?)")
            return

        #wipe the old melody notes
        melody_inst.notes = []

        #write the new melody into that FIRST melodic track
        for (pitch, start, end) in note_events:
            melody_inst.notes.append(pretty_midi.Note(
                velocity=90,
                pitch=pitch,
                start=start,
                end=end
            ))

        midi.write(output_filepath)
        print(f"Saved enhanced file with rhythm  {output_filepath}")

    #this helper samples intervals from the Bayesian model
    def sample_interval(interval_probs):
        if not interval_probs:
            return random.choice([-2, -1, 1, 2])

        intervals = list(interval_probs.keys())
        weights = list(interval_probs.values())
        return random.choices(intervals, weights=weights, k=1)[0]

    #this function enhances the melody
    #it uses the interval probabilities (computed using Bayes theorem in midi_trainer.py)
    #to choose notes
    def enhance_melody_with_intervals_and_rhythm(midi_data, key_name, interval_probs, insert_prob):

        #pull out the melody notes from the MIDI file (with timing)
        melody = []
        for inst in midi_data.instruments:
            if inst.is_drum:
                continue
            for n in inst.notes:
                melody.append((n.pitch, n.start, n.end))

        #sort notes by time so everything is in order
        melody.sort(key=lambda x: x[1])

        enhanced = []

        for i, (pitch, start, end) in enumerate(melody):

            #always keep the original note
            enhanced.append((pitch, start, end))

            #if this is the last note, nothing to insert after it
            if i == len(melody) - 1:
                break

            next_pitch, next_start, next_end = melody[i + 1]

            #decide if we should insert notes between this note and the next
            if random.random() > insert_prob:
                continue

            #how much space exists between notes
            gap = next_start - start


            if gap < 0.35:
                continue

            #decide how many subdivisions to split the gap into (2,3,4 etc.)
            divisions = random.choice([2, 3, 4])
            step = gap / divisions

            #keep track of the last pitch so intervals feel connected
            running_pitch = pitch

            #add dividing notes
            for d in range(1, divisions):

                #pick an interval using our learned interval distribution
                interval = midi_enhancement.sample_interval(interval_probs)

                #if the phrase moves upward, bias interval upward
                direction = 1 if next_pitch > pitch else -1
                interval *= direction

                new_pitch = running_pitch + interval

                #keep pitch valid
                new_pitch = max(0, min(127, new_pitch))

                #snap to the key
                new_pitch = midi_enhancement.correct_notes_to_key([new_pitch], key_name)[0]

                insert_start = end + step * d
                insert_end = insert_start + (step * 0.8)

                enhanced.append((new_pitch, insert_start, insert_end))

                running_pitch = new_pitch

        enhanced.sort(key=lambda x: x[1])
        return enhanced
