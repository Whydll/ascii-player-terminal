# 🎞️ ASCII Player - Terminal

**ASCII Player** is a terminal-based application that converts videos into live-streamed ASCII characters, complete with optional audio playback and color support.

![ascii](https://github.com/user-attachments/assets/64138c31-23d7-4281-b2ba-20d2d6e9c3a3)



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
