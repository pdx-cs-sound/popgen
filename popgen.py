import argparse, random, re
import numpy as np
import sounddevice as sd

# 11 canonical note names.
names = [ "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B", ]

note_names = { s : i for i, s in enumerate(names) }

note_name_re = re.compile(r"([A-G]b?)(\[([0-8])\])?")

def parse_note(s):
    m = note_name_re.fullmatch(s)
    if m is None:
        raise ValueError
    s = m[1]
    q = 4
    if m[3] is not None:
        q = int(m[3])
    return note_names[s] + 12 * q

ap = argparse.ArgumentParser()
ap.add_argument('--bpm', type=int, default=90)
ap.add_argument('--samplerate', type=int, default=48_000)
ap.add_argument('--root', type=parse_note, default="Eb[4]")
ap.add_argument("--test", action="store_true", help=argparse.SUPPRESS)
args = ap.parse_args()

# Tempo in beats per minute.
bpm = args.bpm

# Audio sample rate in samples per second.
samplerate = args.samplerate

# Samples per beat.
beat_samples = int(np.round(samplerate / (bpm / 60)))

# Relative notes of a major scale.
major_scale = [0, 2, 4, 5, 7, 9, 11]

# Major chord scale tones — one-based.
major_chord = [1, 3, 5]

# Given a scale note with root note 0, return a key offset
# from the corresponding root MIDI key.
def note_to_key_offset(note):
    scale_degree = note % 7
    return note // 7 * 12 + major_scale[scale_degree]

# Given a position within a chord, return a scale note
# offset — zero-based.
def chord_to_note_offset(posn):
    chord_posn = posn % 3
    return posn // 3 * 7 + major_chord[chord_posn] - 1

# MIDI key where melody goes.
melody_root = args.root

# Bass MIDI key is below melody root.
bass_root = melody_root - 24

# Root note offset for each chord in scale tones — one-based.
chord_loop = [8, 5, 6, 4]

position = 0
def pick_notes(chord_root, n=4):
    global position
    p = position

    notes = []
    for _ in range(n):
        chord_note_offset = chord_to_note_offset(p)
        chord_note = note_to_key_offset(chord_root + chord_note_offset)
        notes.append(chord_note)

        if random.random() > 0.5:
            p = p + 1
        else:
            p = p - 1

    position = p
    return notes

def make_note(key, n=1):
    f = 440 * 2 ** ((key - 69) / 12)
    b = beat_samples * n
    cycles = 2 * np.pi * f * b / samplerate
    t = np.linspace(0, cycles, b)
    return np.sin(t)

def play(sound):
    sd.play(sound, samplerate=samplerate, blocking=True)
        
if args.test:
    note_tests = [
        (-9, -15),
        (-8, -13),
        (-7, -12),
        (-6, -10),
        (-2, -3),
        (-1, -1),
        (0, 0),
        (6, 11),
        (7, 12),
        (8, 14),
        (9, 16),
    ]

    for n, k in note_tests:
        k0 = note_to_key_offset(n)
        assert k0 == k, f"{n} {k} {k0}"

    chord_tests = [
        (-3, -7),
        (-2, -5),
        (-1, -3),
        (0, 0),
        (1, 2),
        (2, 4),
        (3, 7),
        (4, 9),
    ]

    for n, c in chord_tests:
        c0 = chord_to_note_offset(n)
        assert c0 == c, f"{n} {c} {c0}"

    exit(0)
    
sound = np.array([], dtype=np.float64)
for c in chord_loop:
    notes = pick_notes(c - 1)
    melody = np.concatenate(list(make_note(i + melody_root) for i in notes))

    bass_note = note_to_key_offset(c - 1)
    bass = make_note(bass_note + bass_root, n=4)

    sound = np.append(sound, 0.4 * melody + 0.6 * bass)

play(0.6 * sound)