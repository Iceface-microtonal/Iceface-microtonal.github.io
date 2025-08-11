Iceface Tuning — distribution files
=====================================
Name: Iceface Tuning (black keys +50c)

Definition
----------
12-TET based system where only the black keys (C#, D#, F#, G#, A#) are raised by +50 cents.
Cents: 0,150,200,350,400,500,650,700,850,900,1050,1100,1200

Files
-----
- Iceface_Tuning.scl  : Scala scale file (importable in Scala/MTS-ESP/Surge XT/Vital etc.)
- Iceface_Tuning.tun  : AnaMark-style .tun with 128 absolute frequencies (A4=440Hz). If your synth expects a different TUN flavor, tell me and I'll regenerate.
- Iceface_Tuning_cents.txt : Plain cents list (for quick reference).

Usage notes
-----------
- For MTS-ESP Suite: simply import the .scl file. No special .mts file is required.
- For hosts that accept .tun (AnaMark-compatible): load Iceface_Tuning.tun. Some plugins use slightly different .tun dialects; if it fails, specify the target plugin and I'll export an exact match.
- Reference is A4=440Hz with octave = 1200 cents.

Author
------
H. Wakabayashi (Iceface)
