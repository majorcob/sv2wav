#!/usr/bin/env python
# JACOB CAZABON 2020

desc = """
Command-line utility for automating export of .sunvox projects to .wav.
"""

import argparse
from ctypes import *
import os
import re
from struct import pack
from sys import argv, exit

# Check for “valid” SunVox project file
def is_project(value):
    s = str(value)
    if not s.endswith(".sunvox") or not os.path.isfile(s):
        raise argparse.ArgumentTypeError(f"\"{s}\" is not a valid SunVox file")
    return s

# Set up command-line options
parser = argparse.ArgumentParser(description=desc.strip())
parser.add_argument("infile", type=is_project,
    help="SunVox project file (.sunvox)")
parser.add_argument("-o", "--out", type=str, metavar="FILENAME",
    help="output .wav file")
parser.add_argument("-s", "--sample", type=int, default=44100, metavar="RATE",
    help="audio sampling rate, in Hz [default 44100]")
parser.add_argument("-b", "--buffer", type=int, default=1024, metavar="SIZE",
    help="buffer size, in frames [default 1024]")
parser.add_argument("--bytes", type=int, default=2, choices=[2, 4],
    help="bytes per sample: 2=int16, 4=float32 [default 2]")
args = parser.parse_args()

# Config from arguments
infile = args.infile
outfile = args.out or re.sub(r"\.sunvox$", ".wav", args.infile)
sample = args.sample
buf_frames = args.buffer

# Load Sunvox DLL
dll_path = "./sunvox_dll/windows/lib_x86"
if sizeof(c_void_p) == 8:   # Load 64-bit DLL on 64-bit Python
    dll_path += "_64"
dll_path += "/sunvox.dll"
sv = WinDLL(dll_path)

# Init SunVox with flags
init_flags = (0
    | 1                 # SV_INIT_FLAG_NO_DEBUG_OUTPUT
    | 2                 # SV_INIT_FLAG_USER_AUDIO_CALLBACK
    | 16                # SV_INIT_FLAG_ONE_THREAD
)
if args.bytes == 2:
    init_flags |= 4    # SV_INIT_FLAG_AUDIO_INT16
elif args.bytes == 4:
    init_flags |= 8    # SV_INIT_FLAG_AUDIO_FLOAT32
init_version = sv.sv_init(None, c_int(sample), 2, c_int(init_flags))
if init_version < 0:
    print("sv_init() error {}".format(init_version))
    exit(1)

# Load project
sv.sv_open_slot(0)
load_status = sv.sv_load(0, c_char_p(infile.encode()))  # Load into slot 0
if load_status != 0:
    print("sv_load() error {}".format(load_status))
    exit(1)
sv.sv_volume(0, 256)
sv.sv_play_from_beginning(0)

# Export to WAV
with open(outfile, "wb") as f:

    frame_size = 2 * args.bytes
    buf_size = buf_frames * frame_size
    song_frames = sv.sv_get_song_length_frames(0)
    song_size = song_frames * frame_size

    # WAV header
    f.write("RIFF".encode())
    f.write(pack("l", 4 + 24 + 8 + song_size))  # File size
    f.write("WAVE".encode())

    # Format chunk
    f.write("fmt ".encode())
    f.write(pack("LHHLLHH",
        16,                     # Chunk size
        args.bytes - 1,         # Format (1 for PCM, 3 for float)
        2,                      # Channels; only stereo supported by SunVox lib
        sample,                 # Sample rate per second
        sample * frame_size,    # Bytes per second
        frame_size,             # Data block size
        args.bytes * 8          # Bits per sample
    ))

    # Data section
    f.write("data".encode())
    f.write(pack("l", song_size))
    pos = frame = 0
    _buf = create_string_buffer(buf_frames * frame_size)
    while frame < song_frames:

        # Load next frames into buffer
        frame_count = buf_frames
        if frame + frame_count > song_frames:   # Handle remainder near end
            frame_count = song_frames - frame
        sv.sv_audio_callback(_buf, frame_count, 0, sv.sv_get_ticks())
        frame += frame_count

        # Write buffer to file
        f.write(bytes(_buf))

print("\t{} -> {}".format(infile, outfile))

# Clean up
sv.sv_stop(0)
sv.sv_close_slot(0)
sv.sv_deinit()