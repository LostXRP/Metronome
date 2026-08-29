<div align="center">

Metronome

Precision OSRS timing utility for Windows

A modern desktop metronome built for prayer-flick practice, tick timing, and repeatable rhythm training.

</div>

Overview

Metronome is a lightweight desktop utility designed around Old School RuneScape's 0.6-second game tick. The interface provides an accurate audio cue, a visual pulse, quick tick presets, a global start/stop hotkey, and persistent settings in a compact dark UI.

The default 1-tick preset is 100 BPM. Additional presets are included for 2-tick, 3-tick, and 4-tick timing.

Features

Precision beat scheduling using time.perf_counter

20 to 240 BPM range

OSRS tick presets:

1 tick: 100 BPM

2 ticks: 50 BPM

3 ticks: 33.33 BPM

4 ticks: 25 BPM

Global Ctrl + Shift + C start/stop hotkey

Audio on/off control

Visual pulse on/off control

Adjustable volume

Custom audio file support

Always-on-top mode

Compact overlay mode

Persistent settings

Included default tick sound

Windows executable build script

Requirements

Windows 10 or Windows 11

Python 3.10 or newer

Installation

Clone the repository:

git clone https://github.com/LostXRP/Metronome.git
cd Metronome

Install dependencies:

python -m pip install -r requirements.txt

Run the application:

python Metronome.py

You can also double-click run.bat after installing Python.

Controls

Control

Action

Ctrl + Shift + C

Start or stop the metronome

+ / -

Adjust BPM by one

BPM slider

Fine tempo adjustment

1-4 tick presets

Jump to common OSRS timing intervals

Audio

Enable or disable the tick sound

Visual pulse

Enable or disable the pulse animation

Always on top

Keep Metronome above other windows

Compact mode

Reduce the interface to the essential controls

Custom Sounds

Use Choose in the Sound panel to select a WAV, OGG, or MP3 file supported by Pygame.

Use Reset to return to the included default tick.

Build a Windows Executable

Run:

build.bat

The packaged executable will be written to:

dist\Metronome.exe

The build uses PyInstaller and includes the CustomTkinter resources and default tick sound.

Project Structure

Metronome/
├── assets/
│   └── tick.wav
├── .gitignore
├── build.bat
├── LICENSE
├── Metronome.py
├── README.md
├── requirements.txt
└── run.bat

Notes

Metronome is a timing and practice utility. It does not interact with the RuneScape client, automate clicks, read game memory, or perform gameplay actions.

License

Released under the MIT License.

<div align="center">

Built by LostXRP

</div>
