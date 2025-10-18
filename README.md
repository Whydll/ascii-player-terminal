# 🎞️ ASCII Player - Terminal

**ASCII Player** is a terminal-based app that converts videos into live-streamed ASCII characters.

---

## 🚀 Features

- 🎬 Plays videos as animated ASCII characters in real time
- ⚙️ Adjustable width, FPS,
- 📂 You can upload your own videos
- 💾 Save current ASCII frame as `.txt`
- 🌐 Written in py

---

## Requirements

- Python 3.8+

- FFmpeg, ffprobe, ffplay (for video processing and audio playback)

## Install

Clone the repo

```bash
git clone https://github.com/Whydll/ascii-player-terminal
cd ascii-player-terminal
```

## Running the player

```bash
chmod +x main.py
```

then

```bash
./main.py
```

or

```bash
python3 main.py
```

## Command-line options

- --cols : Number of columns (width) in terminal

- --fps : Video FPS

- --color : Enable truecolor output

- --invert : Invert ASCII characters

- --no-fit : Disable auto-fit to terminal size

- --no-audio : Disable audio playback

```bash
# Example
python main.py --cols 140 --fps 30 --color
```

## Controls (during playback)

| Key         | Function                                      |
| ----------- | --------------------------------------------- |
| `Space`     | Pause / Resume                                |
| `q` / `ESC` | Quit                                          |
| `+` / `-`   | Increase / Decrease columns                   |
| `f`         | Toggle fit (resize to terminal)               |
| `p`         | Toggle color / monochrome                     |
| `w`         | Save current ASCII frame to `ascii_saved.txt` |

## ⚖️ License

Distributed under the MIT License. See [LICENSE.txt](https://github.com/Whydll/ascii-player-terminal/blob/main/LICENSE) for more information.
