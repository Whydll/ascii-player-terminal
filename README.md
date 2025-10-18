# 🎞️ ASCII Player - Terminal

**ASCII Player** is a terminal-based application that converts videos into live-streamed ASCII characters, complete with optional audio playback and color support.

<img src="./videos/ascii.gif" width="300" alt="ASCII Player Demo">

---

## 🚀 Features

- 🎬 Play videos as animated ASCII characters in real time
- ⚙️ Adjustable width (columns), FPS, and character set
- 📂 Upload and play your own videos
- 💾 Save the current ASCII frame as a `.txt` file
- 🌈 Optional colorized output
- 🌐 Written in Python

---

## Requirements

- **Python 3.8+**
- **FFmpeg, ffprobe, ffplay** (for video processing and audio playback)

### Installation

Clone the repository:

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
./main.py --cols 140 --fps 30 --color
```

or

```bash
python3 main.py --cols 140 --fps 30 --color
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

## Color Support Notice

- The colorized output relies on your terminal's truecolor support. Some terminals may **not display colors correctly** or may show only basic 16/256 colors. If colors look incorrect, try disabling color output.

## ⚖️ License

Distributed under the MIT License. See [LICENSE.txt](./LICENSE) for more information.
