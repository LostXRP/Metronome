<div align="center">

# Metronome

### Precision OSRS Timing Utility

A lightweight desktop metronome built for accurate tick timing, prayer flick practice, and repeatable rhythm training in Old School RuneScape.

<br>

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=for-the-badge&logo=windows11&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-111111?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-7C3AED?style=for-the-badge)

<br>



</div>

---

## Overview

**Metronome** is a modern timing utility designed around Old School RuneScape's **0.6 second game tick**.

It provides precise audio cues, a visual pulse, adjustable BPM controls, OSRS tick presets, a global hotkey, custom sounds, persistent settings, and a compact overlay mode.

The application runs completely locally and does not interact with the RuneScape client.

---

## Features

<table>
<tr>
<td width="50%" valign="top">

### Timing

- Precision scheduling with `time.perf_counter`
- Adjustable range from **20 to 240 BPM**
- Fine BPM control
- Instant OSRS tick presets
- High-resolution beat timing

</td>
<td width="50%" valign="top">

### Interface

- Modern dark desktop UI
- Visual beat pulse
- Compact overlay mode
- Always-on-top support
- Saved settings between launches

</td>
</tr>

<tr>
<td width="50%" valign="top">

### Audio

- Included default tick sound
- Adjustable volume
- Audio toggle
- Custom WAV, OGG, and MP3 support
- Reset to default sound

</td>
<td width="50%" valign="top">

### Controls

- Global start and stop hotkey
- BPM slider
- Manual BPM input
- Increment and decrement controls
- One-click timing presets

</td>
</tr>
</table>

---

## OSRS Tick Presets

Old School RuneScape operates on a **0.6 second game tick**.

| Timing | BPM | Interval |
|:---|---:|---:|
| **1 Tick** | `100 BPM` | `0.6s` |
| **2 Ticks** | `50 BPM` | `1.2s` |
| **3 Ticks** | `33.33 BPM` | `1.8s` |
| **4 Ticks** | `25 BPM` | `2.4s` |

The default preset is **100 BPM**, matching one OSRS game tick.

---

## Requirements

Before running Metronome, make sure you have:

- Windows 10 or Windows 11
- Python 3.10 or newer
- `pip`
- The dependencies listed in `requirements.txt`

Check your Python installation:

```bash
python --version
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/LostXRP/Metronome.git
cd Metronome
```

### 2. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Launch Metronome

```bash
python Metronome.py
```

---

## Launch Without Opening a Terminal

A launcher BAT file is intentionally not included in the repository.

If you prefer to launch Metronome by double-clicking a file, you can create your own.

### Create a BAT Launcher

1. Open **Notepad**
2. Paste the following:

```bat
@echo off
cd /d "%~dp0"
python Metronome.py
pause
```

3. Select **File > Save As**
4. Change **Save as type** to `All Files`
5. Name the file:

```text
Launch Metronome.bat
```

6. Save it in the same directory as `Metronome.py`
7. Double-click the BAT file to launch Metronome

### Launch Without a Console Window

Use this version instead:

```bat
@echo off
cd /d "%~dp0"
start "" pythonw Metronome.py
exit
```

Python must be installed and available through your system PATH.

---

## Controls

| Control | Function |
|:---|:---|
| `Ctrl + Shift + C` | Start or stop the metronome |
| `+` | Increase BPM |
| `-` | Decrease BPM |
| BPM field | Enter an exact BPM |
| BPM slider | Fine tempo adjustment |
| 1 Tick | Set tempo to 100 BPM |
| 2 Ticks | Set tempo to 50 BPM |
| 3 Ticks | Set tempo to 33.33 BPM |
| 4 Ticks | Set tempo to 25 BPM |
| Audio | Enable or disable sound |
| Visual Pulse | Enable or disable pulse animation |
| Always On Top | Keep the utility above other windows |
| Compact Mode | Reduce the interface to essential controls |

---

## Custom Sounds

Metronome includes a default tick sound located at:

```text
assets/tick.wav
```

You can select your own supported audio file from inside the application.

Supported formats include:

```text
.wav
.ogg
.mp3
```

Select **Reset** at any time to return to the bundled default sound.

---

## Build a Windows Executable

Metronome includes a build script for packaging the application into a standalone Windows executable.

Run:

```bat
build.bat
```

The build process installs PyInstaller if required and creates:

```text
dist\Metronome.exe
```

The executable includes the required CustomTkinter resources and bundled tick sound.

---

## Project Structure

```text
Metronome/
│
├── assets/
│   └── tick.wav
│
├── .gitignore
├── build.bat
├── LICENSE
├── Metronome.py
├── README.md
└── requirements.txt
```

---

## Dependencies

| Package | Purpose |
|:---|:---|
| `customtkinter` | Modern desktop interface |
| `pygame` | Audio playback |
| `keyboard` | Global hotkey support |

Install everything with:

```bash
python -m pip install -r requirements.txt
```

---

## Privacy

Metronome runs locally on your computer.

It does not:

- Connect to the RuneScape client
- Read game memory
- Automate mouse clicks
- Automate keyboard input
- Access your RuneScape account
- Send gameplay information anywhere
- Require an account or API key

---

## Disclaimer

Metronome is an independent timing and practice utility.

It is not affiliated with, endorsed by, or associated with Jagex Ltd. or Old School RuneScape.

RuneScape and Old School RuneScape are trademarks of Jagex Ltd.

---

## License

This project is licensed under the **MIT License**.

See [`LICENSE`](LICENSE) for full license terms.

---

<div align="center">

### LostXRP

**Crypto • Development • Web3**

</div>
