# C3 MIDI Detector Max for Live Patch

`C3_MIDI_Detector.maxpat` is a Max 8 patch intended for a Max for Live MIDI
Effect device in Ableton Live.

## What it does

- Receives MIDI from the track with `notein`.
- Passes all incoming MIDI through unchanged with `noteout`.
- Uses `stripnote` to ignore note-off messages.
- Detects C3 with `sel 60`.
- Flashes the UI toggle for 150 ms whenever C3 is played.

Ableton names MIDI note number 60 as C3. If your Max setup labels octaves
differently, edit the `sel 60` object to the note number you want to detect.

## How to use in Ableton Live

1. Create a Max for Live MIDI Effect device.
2. Open the device in Max 8.
3. Copy the contents of `C3_MIDI_Detector.maxpat` into the device patcher, or
   open this patch and save it from Max as a Max for Live MIDI Effect.
4. Place the device before an instrument on a MIDI track.
5. Play C3; the "C3 detected" toggle will light briefly.
