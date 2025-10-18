#!/usr/bin/env python3
"""
ascii_player_sync_audio.py
Terminal ASCII video player with synchronized audio.

Usage:
  python3 ascii_player_sync_audio.py [source] [--cols N] [--fps N] [--color] [--no-fit]

If source is omitted, lists files in videos/ and asks for selection.

Dependencies:
  - ffmpeg, ffprobe, ffplay
  - numpy

Install on Debian/Ubuntu:
  sudo apt install ffmpeg
  pip install numpy
"""
import argparse, subprocess, sys, os, shutil, time, threading, termios, tty, select, glob
import numpy as np
from shutil import get_terminal_size

# ---------- CONFIG ----------
CHARSETS = [
    " .:-=+*#%@",
    "@%#*+=-:. ",
    "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^'`."
]
CHAR_RATIO_DEFAULT = 0.32
COLS_STEP = 8
MAX_COLS = 320
MIN_COLS = 20

# ---------- helpers ----------
def has_prog(name):
    return shutil.which(name) is not None

def probe_size(src):
    cmd = ["ffprobe","-v","error","-select_streams","v:0",
           "-show_entries","stream=width,height","-of","csv=p=0:s=x", src]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        return None, None
    out = p.stdout.strip()
    if "x" in out:
        w,h = out.split("x")
        return int(w), int(h)
    return None, None

def start_video_proc(src, start_time, w, h, fps):
    # -ss before -i for fast seek
    cmd = [
        "ffmpeg", "-ss", str(start_time), "-i", src,
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-vf", f"scale={w}:{h}",
        "-r", str(fps),
        "-hide_banner", "-loglevel", "error", "-"
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**7)

def start_audio_proc(src, start_time):
    # ffplay used for audio; -ss before -i to seek
    cmd = ["ffplay", "-ss", str(start_time), "-nodisp", "-autoexit", "-loglevel", "error", src]
    # run detached from stdout
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def luminance(rgb):
    r = rgb[...,0].astype(np.float32)
    g = rgb[...,1].astype(np.float32)
    b = rgb[...,2].astype(np.float32)
    return (0.2126*r + 0.7152*g + 0.0722*b) / 255.0

# ANSI helpers
CSI = "\x1b["
def clear_screen(): sys.stdout.write(CSI + "2J" + CSI + "H")
def home_cursor(): sys.stdout.write(CSI + "H")
def hide_cursor(): sys.stdout.write(CSI + "?25l")
def show_cursor(): sys.stdout.write(CSI + "?25h")
def ansi_rgb(r,g,b): return f"\x1b[38;2;{r};{g};{b}m"
def reset_color(): return "\x1b[0m"

# ---------- non-blocking key reader ----------
class KeyReader(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        self.running = True
        self.lock = threading.Lock()
        self.last = None

    def run(self):
        tty.setcbreak(self.fd)
        while self.running:
            dr,_,_ = select.select([self.fd], [], [], 0.05)
            if dr:
                try:
                    data = os.read(self.fd, 4)
                except:
                    data = b''
                if not data:
                    continue
                try:
                    s = data.decode('utf-8', errors='ignore')
                except:
                    s = ''
                with self.lock:
                    self.last = s
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)

    def get(self):
        with self.lock:
            k = self.last
            self.last = None
            return k

    def stop(self):
        self.running = False

# ---------- Player (video + audio sync by restarting processes on pause/resume/seek/resize) ----------
def play(src, cols, fps, charset_idx, invert, char_ratio, use_color, fit, audio_enabled):
    vw, vh = probe_size(src)
    term_w, term_h = get_terminal_size()
    cols = max(MIN_COLS, min(cols, term_w))

    def compute_rows_for_cols(c):
        if vw and vh:
            scale = vw / c
            rows = max(2, int(round(vh / scale / char_ratio)))
        else:
            rows = max(2, int(round(c * 0.5 * char_ratio)))
        tw, th = get_terminal_size()
        allowed = max(4, th - 2)
        if rows > allowed:
            rows = allowed
        return rows

    def fit_to_terminal():
        tw, th = get_terminal_size()
        c = min(MAX_COLS, max(MIN_COLS, tw))
        r = compute_rows_for_cols(c)
        allowed = max(4, th - 2)
        if r > allowed:
            # reduce cols proportionally
            factor = allowed / r
            c = max(MIN_COLS, int(c * factor))
            r = compute_rows_for_cols(c)
        return c, r

    # initial sizing
    if fit:
        cols, rows = fit_to_terminal()
    else:
        rows = compute_rows_for_cols(cols)

    # state
    current_charset = CHARSETS[charset_idx % len(CHARSETS)]
    charset_len = len(current_charset)
    frame_size = cols * rows * 3
    frame_count = 0
    start_time = 0.0  # start time offset in seconds (for resumes)
    playing = True
    paused = False
    last_lines = []
    last_time = time.time()

    video_proc = None
    audio_proc = None

    def start_procs(at_time):
        nonlocal video_proc, audio_proc, frame_size
        # safe terminate existing
        try:
            if video_proc:
                video_proc.terminate()
        except: pass
        try:
            if audio_proc:
                audio_proc.terminate()
        except: pass
        # start new video proc
        video_proc = start_video_proc(src, at_time, cols, rows, fps)
        frame_size = cols * rows * 3
        # start audio if enabled and ffplay exists
        audio_proc = None
        if audio_enabled:
            if has_prog("ffplay"):
                audio_proc = start_audio_proc(src, at_time)
            else:
                # if audio requested but ffplay missing, just ignore audio
                pass

    # start initial processes
    start_procs(start_time)

    kr = KeyReader(); kr.start()
    hide_cursor(); clear_screen()

    try:
        while playing:
            # handle fit / resize dynamic
            tw, th = get_terminal_size()
            if fit:
                new_cols, new_rows = fit_to_terminal()
                if new_cols != cols or new_rows != rows:
                    # compute current playback time to resume correctly
                    curr_time = frame_count / max(1, fps)
                    cols, rows = new_cols, new_rows
                    frame_size = cols * rows * 3
                    # restart procs at curr_time
                    start_procs(curr_time)

            # read user key
            k = kr.get()
            if k:
                ch = k
                if ch in ('q', '\x1b'):
                    playing = False
                    break
                if ch == ' ':
                    # toggle pause: kill procs (pause) or restart at current time (resume)
                    if not paused:
                        # pause: compute current time then kill procs
                        paused = True
                        # compute approximate current time from frames read
                        curr_time = frame_count / max(1, fps)
                        # terminate procs
                        try:
                            if video_proc: video_proc.terminate()
                        except: pass
                        try:
                            if audio_proc: audio_proc.terminate()
                        except: pass
                        video_proc = None
                        audio_proc = None
                        # quick HUD update
                        home_cursor(); sys.stdout.write(f"[PAUSED] t={curr_time:.2f}s cols={cols} rows={rows} color={use_color}\n"); sys.stdout.flush()
                    else:
                        # resume: restart procs from current_time
                        paused = False
                        # we resume from frame_count / fps (this approximates the time)
                        start_time = frame_count / max(1, fps)
                        start_procs(start_time)
                if ch in ('+', '='):
                    fit = False
                    # increase cols
                    cols = min(MAX_COLS, cols + COLS_STEP)
                    rows = compute_rows_for_cols(cols)
                    frame_size = cols * rows * 3
                    # restart procs at current time
                    curr_time = frame_count / max(1, fps)
                    start_procs(curr_time)
                if ch in ('-', '_'):
                    fit = False
                    cols = max(MIN_COLS, cols - COLS_STEP)
                    rows = compute_rows_for_cols(cols)
                    frame_size = cols * rows * 3
                    curr_time = frame_count / max(1, fps)
                    start_procs(curr_time)
                if ch == 'f':
                    fit = not fit
                    if fit:
                        cols, rows = fit_to_terminal()
                        frame_size = cols * rows * 3
                        curr_time = frame_count / max(1, fps)
                        start_procs(curr_time)
                if ch == 'p':
                    use_color = not use_color
                if ch == 'w':
                    try:
                        with open("ascii_saved.txt", "w", encoding="utf-8") as f:
                            f.write("\n".join(last_lines))
                        home_cursor(); sys.stdout.write("[saved -> ascii_saved.txt]\n"); sys.stdout.flush()
                    except Exception as e:
                        home_cursor(); sys.stdout.write(f"[save error: {e}]\n"); sys.stdout.flush()

            if paused:
                time.sleep(0.05)
                continue

            # read one frame from video_proc
            if not video_proc:
                # safety: if process missing, try to restart at current time
                curr_time = frame_count / max(1, fps)
                start_procs(curr_time)
                if not video_proc:
                    # can't start video proc -> abort
                    print("Video process başlatılamıyor. Çıkılıyor.")
                    break

            buf = b''
            toread = frame_size
            # read exactly a frame worth of bytes
            while toread:
                chunk = video_proc.stdout.read(toread)
                if not chunk:
                    # end of stream
                    playing = False
                    break
                buf += chunk
                toread -= len(chunk)
            if not playing or len(buf) < frame_size:
                break

            # convert to array
            arr = np.frombuffer(buf, dtype=np.uint8)
            try:
                arr = arr.reshape((rows, cols, 3))
            except Exception:
                # shape mismatch -> likely ended
                break

            # convert to ascii lines
            y = luminance(arr)
            idxs = np.floor(y * (charset_len - 1)).astype(np.int32)
            if invert:
                idxs = (charset_len - 1) - idxs

            lines = []
            for r in range(rows):
                row_rgb = arr[r]
                row_idx = idxs[r]
                if use_color:
                    parts = []
                    lastc = None
                    for x in range(cols):
                        ch = current_charset[row_idx[x]]
                        R,G,B = int(row_rgb[x,0]), int(row_rgb[x,1]), int(row_rgb[x,2])
                        ccode = (R,G,B)
                        if ccode != lastc:
                            parts.append(ansi_rgb(R,G,B))
                            lastc = ccode
                        parts.append(ch)
                    parts.append(reset_color())
                    lines.append("".join(parts))
                else:
                    # monochrome
                    chars = [current_charset[i] for i in row_idx]
                    lines.append("".join(chars))

            last_lines = lines

            # render to terminal
            home_cursor()
            hud = f" src:{os.path.basename(src)} | cols:{cols} rows:{rows} fps:{fps} color:{use_color} fit:{fit} (space pause/resume, q quit)"
            sys.stdout.write(hud + "\n")
            for ln in lines:
                sys.stdout.write(ln + "\n")
            sys.stdout.flush()

            frame_count += 1
            # frame timing (we read from ffmpeg at fps; maintain rough sleep to avoid runaway)
            frame_interval = 1.0 / fps
            now = time.time()
            elapsed = now - last_time
            sleep_time = max(0, frame_interval - elapsed)
            time.sleep(sleep_time)
            last_time = time.time()


    finally:
        kr.stop()
        show_cursor()
        try:
            if video_proc:
                video_proc.terminate()
        except: pass
        try:
            if audio_proc:
                audio_proc.terminate()
        except: pass
        sys.stdout.write(reset_color())
        sys.stdout.flush()

# ---------- entrypoint ----------
def main():
    if not has_prog("ffmpeg") or not has_prog("ffprobe"):
        print("ffmpeg ve ffprobe bulunamadı. Lütfen yükleyin."); sys.exit(1)

    p = argparse.ArgumentParser(description="ASCII video player with synchronized audio")
    p.add_argument("source", nargs="?", help="Video dosyası veya URL (ffmpeg ile okunabilir)")
    p.add_argument("--cols", type=int, default=120)
    p.add_argument("--fps", type=int, default=12)
    p.add_argument("--charset", type=int, default=0, help="Charset index")
    p.add_argument("--invert", action="store_true")
    p.add_argument("--char-ratio", type=float, default=CHAR_RATIO_DEFAULT)
    p.add_argument("--color", action="store_true", help="Enable truecolor output")
    p.add_argument("--no-fit", dest="fit", action="store_false", help="Disable auto-fit")
    p.add_argument("--no-audio", dest="audio", action="store_false", help="Disable audio (default: enabled if ffplay present)")
    args = p.parse_args()

    src = args.source
    if not src:
        # list videos/ folder
        files = sorted(glob.glob("videos/*.*"))
        if not files:
            print("videos/ klasöründe video bulunamadı. Kaynak belirtin veya videolar ekleyin.")
            return
        print("Videolar (videos/):")
        for i,f in enumerate(files, start=1):
            print(f" {i}. {os.path.basename(f)}")
        sel = input("Numara seç (veya boş: iptal): ").strip()
        if not sel:
            print("İptal."); return
        try:
            idx = int(sel) - 1
            src = files[idx]
        except Exception:
            print("Geçersiz seçim."); return

    audio_enabled = True
    if args.audio is False:
        audio_enabled = False
    else:
        # default true if ffplay exists
        audio_enabled = has_prog("ffplay")

    play(src, args.cols, args.fps, args.charset, args.invert, args.char_ratio, args.color, args.fit, audio_enabled)

if __name__ == "__main__":
    main()
