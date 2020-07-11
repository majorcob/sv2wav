# Vox2Wav

A Python script to automate export of [SunVox](https://www.warmplace.ru/soft/sunvox/) project files. Pretty much just an adaptation of [the library's C examples](https://github.com/warmplace/sunvox_dll/blob/master/examples/c/test4.c) with command-line arguments.

Currently only supports Windows as I don't have access to testing hardware for other platforms.

## Usage

Make sure to `git clone --recursive` to grab the SunVox lib submodule.

```sh
python vox2wav.py [-h] [-o FILENAME] [-s RATE] [-b SIZE] [--bytes {2,4}] infile
```

- `infile`: SunVox project file (`.sunvox`); **required**
- `-o`, `--out`: custom output filename
- `-s`, `--sample`: audio sampling rate, in Hz (default `44100`)
- `-b`, `--buffer`: audio buffer size, in frames (default `1024`)
- `--bytes`: bytes per sample: `2`=PCM, `4`=float (default `2`)