import ctypes
import math
import os
import queue
import re
import threading
import time
import tkinter as tk
import unicodedata
from dataclasses import dataclass, replace
from functools import cached_property
from tkinter import font as tkfont

try:
    import pyautogui
    from pynput import keyboard as pynput_keyboard
    from pynput import mouse as pynput_mouse
except ImportError as exc:
    raise SystemExit(
        "Dependencies are missing. Run START.bat so the required packages can be installed.\n\n"
        f"Details: {exc}"
    )

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None

RESAMPLE_BOX = getattr(Image, "Resampling", Image).BOX if Image is not None else None

APP_NAME = "PonyTown Text Placer"
CREDIT = "Made by Zurá"
IS_WINDOWS = os.name == "nt"

BG = "#0a0a0a"
SURFACE = "#111111"
RAISED = "#171717"
HOVER = "#222222"
PRESSED = "#2c2c2c"
LINE = "#262626"
LINE_STRONG = "#3b3b3b"
FG = "#f2f2f2"
MUTED = "#9b9b9b"
FAINT = "#686868"
INK = "#0a0a0a"

MODE_BALANCED = "balanced"
MODE_AUTO = "auto"
MODE_MAXIMUM = "maximum"
ALIGN_LEFT = "left"
ALIGN_CENTER = "center"
ALIGN_RIGHT = "right"
FONT_DETAILED = "5x7"
FONT_COMPACT = "3x5"

MAX_ITEMS = 5000
DEFAULT_LIMIT = 600
DEFAULT_GAP = 2
DEFAULT_PITCH = 10
DEFAULT_SPEED = 5
DEFAULT_TEXT = "SOREN\nBIHUN"
GAP_RANGE = (0, 8)
PITCH_RANGE = (3, 48)
OFFSET_RANGE = (-30, 30)
SPEED_RANGE = (1, 10)

OVERLAY_ALPHA = 0.65
COUNTDOWN_SECONDS = 5
DWELL_SECONDS = 0.35
TICK_MS = 30
EPSILON = 1e-9
SUPERSAMPLE = 8
INK_THRESHOLD = 0.38
IGNORED_CATEGORIES = ("Cc", "Cf", "Mn", "Me", "Cs")
WINDOWS_FONTS = (
    "segoeui.ttf", "seguisym.ttf", "arial.ttf", "msyh.ttc", "msjh.ttc", "YuGothM.ttc", "YuGothR.ttc",
    "meiryo.ttc", "malgun.ttf", "simsun.ttc", "mingliu.ttc", "Nirmala.ttf", "LeelawUI.ttf", "ebrima.ttf",
    "gadugi.ttf", "himalaya.ttf", "mvboli.ttf", "monbaiti.ttf", "msyi.ttf", "taile.ttf", "javatext.ttf",
    "mmrtext.ttf", "seguihis.ttf", "micross.ttf", "seguiemj.ttf",
)
TYPOGRAPHY = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'", "\u2032": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"', "\u2033": '"',
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2015": "-", "\u2212": "-",
})

# Explicit delays replace PyAutoGUI's implicit per-call pause (disabled in main),
# keeping the click timing the game receives identical and predictable.
MOVE_SETTLE = 0.135
PRESS_HOLD = 0.20
RELEASE_SETTLE = 0.10

FONT_5X7 = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10101", "10011", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00110", "00100"),
    ":": ("00000", "00110", "00110", "00000", "00110", "00110", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "'": ("00100", "00100", "00010", "00000", "00000", "00000", "00000"),
    "\"": ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "%": ("11000", "11001", "00010", "00100", "01000", "10011", "00011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "@": ("01110", "10001", "00001", "01101", "10101", "10101", "01110"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "\\": ("00000", "10000", "01000", "00100", "00010", "00001", "00000"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "^": ("00100", "01010", "10001", "00000", "00000", "00000", "00000"),
    "`": ("01000", "00100", "00010", "00000", "00000", "00000", "00000"),
    "{": ("00110", "00100", "00100", "01000", "00100", "00100", "00110"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "}": ("01100", "00100", "00100", "00010", "00100", "00100", "01100"),
    "~": ("00000", "00000", "01000", "10101", "00010", "00000", "00000"),
    "♥": ("00000", "01010", "11111", "11111", "11111", "01110", "00100"),
    "♡": ("00000", "01010", "10101", "10001", "10001", "01010", "00100"),
    "❤": ("00000", "01010", "11111", "11111", "11111", "01110", "00100"),
}

FONT_3X5 = {
    "A": ("010", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "J": ("001", "001", "001", "101", "010"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("010", "101", "101", "101", "010"),
    "P": ("110", "101", "110", "100", "100"),
    "Q": ("010", "101", "101", "111", "011"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"),
    "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"),
    "Z": ("111", "001", "010", "100", "111"),
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("110", "001", "010", "100", "111"),
    "3": ("110", "001", "010", "001", "110"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "110", "001", "110"),
    "6": ("011", "100", "110", "101", "010"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("010", "101", "010", "101", "010"),
    "9": ("010", "101", "011", "001", "110"),
    ".": ("000", "000", "000", "000", "010"),
    ",": ("000", "000", "000", "010", "100"),
    "!": ("010", "010", "010", "000", "010"),
    "?": ("110", "001", "010", "000", "010"),
    "-": ("000", "000", "111", "000", "000"),
    "_": ("000", "000", "000", "000", "111"),
    "+": ("000", "010", "111", "010", "000"),
    "/": ("001", "001", "010", "100", "100"),
    "&": ("010", "101", "010", "101", "011"),
    "'": ("010", "010", "100", "000", "000"),
    ":": ("000", "010", "000", "010", "000"),
    "\"": ("101", "101", "000", "000", "000"),
    "#": ("101", "111", "101", "111", "101"),
    "$": ("011", "110", "010", "011", "110"),
    "%": ("101", "001", "010", "100", "101"),
    "(": ("001", "010", "010", "010", "001"),
    ")": ("100", "010", "010", "010", "100"),
    "*": ("000", "101", "010", "101", "000"),
    ";": ("000", "010", "000", "010", "100"),
    "<": ("001", "010", "100", "010", "001"),
    "=": ("000", "111", "000", "111", "000"),
    ">": ("100", "010", "001", "010", "100"),
    "@": ("010", "101", "111", "100", "011"),
    "[": ("011", "010", "010", "010", "011"),
    "\\": ("100", "100", "010", "001", "001"),
    "]": ("110", "010", "010", "010", "110"),
    "^": ("010", "101", "000", "000", "000"),
    "`": ("100", "010", "000", "000", "000"),
    "{": ("011", "010", "110", "010", "011"),
    "|": ("010", "010", "010", "010", "010"),
    "}": ("110", "010", "011", "010", "110"),
    "~": ("000", "011", "110", "000", "000"),
    "♥": ("000", "101", "111", "010", "000"),
    "♡": ("000", "101", "101", "010", "000"),
    "❤": ("000", "101", "111", "010", "000"),
}

FONTS = {FONT_DETAILED: FONT_5X7, FONT_COMPACT: FONT_3X5}

STRINGS = {
    "subtitle": ("Ubah teks menjadi pola penempatan berbasis grid.", "Turn text into a grid-based placement pattern."),
    "text_label": ("Teks", "Text"),
    "text_hint": ("Enter menambah baris. Huruf otomatis menjadi kapital.", "Enter adds a line. Letters are converted to uppercase."),
    "limit_total": ("Limit total", "Total limit"),
    "already_placed": ("Sudah terpasang", "Already placed"),
    "line_gap": ("Jarak baris", "Line gap"),
    "grid_mode": ("Mode grid", "Grid mode"),
    "mode_balanced": ("Sesuai", "Balanced"),
    "mode_auto": ("Auto Limit", "Auto limit"),
    "mode_maximum": ("Maksimum", "Maximum"),
    "mode_help_balanced": ("Mempertahankan resolusi dasar pola saat ukuran diubah.", "Keeps the pattern's base resolution as the size changes."),
    "mode_help_auto": ("Kepadatan menyesuaikan ukuran dan sisa limit item.", "Density adapts to size and the remaining item limit."),
    "mode_help_maximum": ("Memakai resolusi tertinggi yang masih muat dalam limit.", "Uses the highest resolution that fits the item limit."),
    "alignment": ("Perataan", "Alignment"),
    "outline": ("Hanya outline", "Outline only"),
    "outline_help": ("Hanya garis tepi karakter. Perbesar pola untuk melihat efeknya.", "Border of each character only. Enlarge the pattern to see the effect."),
    "grid_section": ("Grid dan overlay", "Grid and overlay"),
    "reset": ("Reset", "Reset"),
    "grid_x": ("Grid X", "Grid X"),
    "grid_y": ("Grid Y", "Grid Y"),
    "row_offset": ("Offset baris", "Row offset"),
    "show_overlay": ("Tampilkan overlay", "Show overlay"),
    "hide_overlay": ("Sembunyikan overlay", "Hide overlay"),
    "lock_overlay": ("Kunci overlay", "Lock overlay"),
    "unlock_overlay": ("Buka kunci overlay", "Unlock overlay"),
    "drag_to_move": ("Geser untuk pindah", "Drag to move"),
    "locked_label": ("Terkunci", "Locked"),
    "lock_short": ("Kunci", "Lock"),
    "unlock_short": ("Buka", "Unlock"),
    "repair_short": ("Perbaiki", "Repair"),
    "repair_active_short": ("Memperbaiki", "Repairing"),
    "hide_short": ("Sembunyi", "Hide"),
    "preview": ("Pratinjau", "Preview"),
    "empty_pattern": ("Masukkan teks untuk melihat pola.", "Enter text to preview the pattern."),
    "count": ("{count} dari {available} titik", "{count} of {available} points"),
    "font_detailed": ("Font 5x7 detail", "Font 5x7 detailed"),
    "font_compact": ("Font 3x5 ringkas", "Font 3x5 compact"),
    "click_speed": ("Kecepatan klik", "Click speed"),
    "start": ("Mulai penempatan", "Start placement"),
    "pause": ("Jeda", "Pause"),
    "resume": ("Lanjut", "Resume"),
    "stop": ("Berhenti", "Stop"),
    "ok": ("OK", "OK"),
    "cancel": ("Batal", "Cancel"),
    "yes": ("Ya", "Yes"),
    "no": ("Tidak", "No"),
    "ready": ("Siap. Tulis teks, tampilkan overlay, lalu atur langsung di layar.", "Ready. Enter text, show the overlay, then position it on screen."),
    "not_started": ("Belum mulai", "Not started"),
    "pattern_ready": ("Pola siap.", "Pattern ready."),
    "progress_idle": ("Percobaan {done}/{total}, belum diverifikasi oleh game", "Attempts {done}/{total}, not verified by the game"),
    "progress_run": ("Percobaan {done}/{total}, proses {sent}/{planned}, titik #{point}", "Attempts {done}/{total}, run {sent}/{planned}, point #{point}"),
    "progress_pending": ("Percobaan {done}/{total}, {pending} titik menunggu", "Attempts {done}/{total}, {pending} points pending"),
    "layout_reset": ("Tata letak direset.", "Layout reset."),
    "reset_blocked": ("Hentikan penempatan sebelum mereset tata letak.", "Stop placement before resetting the layout."),
    "overlay_hidden": ("Overlay disembunyikan.", "Overlay hidden."),
    "overlay_locked": ("Overlay terkunci. Klik menembus ke Pony Town.", "Overlay locked. Clicks pass through to Pony Town."),
    "overlay_editing": ("Mode edit. Pegangan kanan atas mengatur lebar, kiri bawah mengatur tinggi.", "Edit mode. The top-right grip adjusts width, the bottom-left grip adjusts height."),
    "overlay_busy": ("Overlay tidak bisa diubah saat penempatan berlangsung.", "The overlay cannot be changed while placement is running."),
    "hide_blocked": ("Selesaikan atau hentikan penempatan sebelum menyembunyikan overlay.", "Finish or stop placement before hiding the overlay."),
    "auto_active": ("Auto Limit aktif. Grid X {x:.2f}x, Y {y:.2f}x, {count}/{available} titik.", "Auto limit active. Grid X {x:.2f}x, Y {y:.2f}x, {count}/{available} points."),
    "limit_reached": ("Batas item tercapai. Grid X {x:.2f}x, Y {y:.2f}x, {count}/{available} titik.", "Item limit reached. Grid X {x:.2f}x, Y {y:.2f}x, {count}/{available} points."),
    "repair_on": ("Mode perbaikan aktif. Tahan kursor di titik kosong sekitar 0,35 detik.", "Repair mode on. Hold the cursor over an empty point for about 0.35 seconds."),
    "repair_off": ("Mode perbaikan dimatikan.", "Repair mode off."),
    "repair_off_edit": ("Mode perbaikan dimatikan agar overlay bisa diedit.", "Repair mode off so the overlay can be edited."),
    "repair_off_hidden": ("Overlay disembunyikan, mode perbaikan dimatikan.", "Overlay hidden, repair mode off."),
    "repair_off_pattern": ("Teks atau pola berubah, mode perbaikan dimatikan. Kunci ulang overlay.", "Text or pattern changed, repair mode off. Lock the overlay again."),
    "repair_off_overlay": ("Mode perbaikan dimatikan untuk mengubah overlay.", "Repair mode off to change the overlay."),
    "repair_blocked": ("Tunggu penempatan selesai sebelum mengubah mode perbaikan.", "Wait for placement to finish before changing repair mode."),
    "repair_no_tracker": ("Pelacakan kursor global tidak tersedia. Periksa instalasi pynput lalu buka ulang aplikasi.", "Global cursor tracking is unavailable. Check the pynput installation and restart the app."),
    "repair_idle": ("Arahkan kursor ke titik kosong yang terlewat.", "Move the cursor over a missed point."),
    "repair_hover": ("Titik #{point}: tahan kursor agar diklik.", "Point #{point}: hold the cursor still to click."),
    "repair_seen": ("Titik #{point} sudah dicoba. Matikan lalu aktifkan mode untuk mengulang.", "Point #{point} was already tried. Toggle the mode to try again."),
    "repair_done": ("Titik #{point}: klik dikirim. Periksa hasilnya di Pony Town.", "Point #{point}: click sent. Check the result in Pony Town."),
    "repair_fail": ("Gagal mengirim klik ke titik #{point}: {error}", "Failed to send click to point #{point}: {error}"),
    "repair_error": ("Mode perbaikan mengalami masalah: {error}", "Repair mode ran into a problem: {error}"),
    "esc_repair_off": ("ESC ditekan, mode perbaikan dimatikan.", "ESC pressed, repair mode off."),
    "err_no_items": ("Tidak ada item tersisa. Kurangi jumlah item terpasang atau naikkan limit.", "No items left. Lower the placed count or raise the limit."),
    "err_no_text": ("Masukkan teks terlebih dahulu.", "Enter some text first."),
    "err_too_big": ("Limit tersisa {available}, tetapi pola paling ringkas membutuhkan {needed} item. Kurangi teks atau baris, atau naikkan limit.", "Only {available} items remain, but the most compact pattern needs {needed}. Shorten the text or raise the limit."),
    "err_calc": ("Tidak dapat menghitung pola: {error}", "Could not calculate the pattern: {error}"),
    "dlg_invalid_title": ("Pola tidak valid", "Invalid pattern"),
    "dlg_overlay_failed_title": ("Overlay gagal", "Overlay error"),
    "dlg_overlay_failed_body": ("Tidak dapat menampilkan overlay.\n\n{error}", "The overlay could not be shown.\n\n{error}"),
    "dlg_need_overlay_title": ("Overlay belum tampil", "Overlay is not visible"),
    "dlg_need_overlay_body": ("Klik Tampilkan overlay, sesuaikan pola, lalu kunci overlay.", "Click Show overlay, adjust the pattern, then lock the overlay."),
    "dlg_need_lock_title": ("Overlay belum dikunci", "Overlay is not locked"),
    "dlg_need_lock_body": ("Atur posisi pola lalu kunci overlay agar klik diteruskan ke Pony Town.", "Position the pattern, then lock the overlay so clicks pass through to Pony Town."),
    "dlg_empty_title": ("Pola kosong", "Empty pattern"),
    "dlg_empty_body": ("Tidak ada titik penempatan dalam pola ini.", "There are no placement points in this pattern."),
    "dlg_repair_title": ("Mode perbaikan aktif", "Repair mode is on"),
    "dlg_repair_body": ("Matikan mode perbaikan sebelum menjalankan pola penuh.", "Turn off repair mode before running the full pattern."),
    "dlg_grid_title": ("Grid berubah", "Grid changed"),
    "dlg_grid_body": ("Ukuran, kerapatan, atau kalibrasi grid berubah sejak progres terakhir. Progres lama tidak lagi cocok. Mulai pola ini dari awal?", "The size, density, or grid calibration changed since the last progress. The old progress no longer matches. Start this pattern from the beginning?"),
    "dlg_done_title": ("Pola sudah dicoba", "Pattern already attempted"),
    "dlg_done_body": ("Semua titik pola sudah pernah dicoba. Mulai ulang akan mengklik titik lagi dan bisa menambah item di lokasi yang sudah terisi. Mulai ulang dari titik pertama?", "Every pattern point has already been attempted. Restarting may place duplicate items on occupied locations. Start again from the first point?"),
    "dlg_nothing_title": ("Tidak ada titik baru", "No new points"),
    "dlg_nothing_body": ("Semua titik yang tersisa sudah pernah dicoba dalam sesi ini. Periksa titik kosong di game, lalu gunakan Perbaiki pada bilah atas overlay.", "Every remaining point was already tried in this session. Check for empty points in the game, then use Repair on the overlay's top bar."),
    "dlg_confirm_title": ("Siap menempatkan item?", "Ready to place items?"),
    "dlg_confirm_body": (
        "{resume}. Aplikasi akan mencoba {pending} titik yang belum pernah dicoba pada sesi ini, dari {total} titik pola.\n\n"
        "Pastikan Pony Town tersambung, mode bangun dan item yang benar aktif, serta overlay pas dengan grid. Klik yang terkirim belum memastikan item berhasil dipasang.\n\n"
        "Setelah OK, pindah ke Pony Town. Proses mulai dalam {seconds} detik. Tekan ESC atau Berhenti untuk menghentikan; progres sesi tetap ada di memori selama aplikasi terbuka.",
        "{resume}. The app will attempt {pending} points not yet attempted in this session, out of {total} pattern points.\n\n"
        "Make sure Pony Town is connected, build mode and the correct item are active, and the overlay matches the grid. A sent click does not confirm item placement.\n\n"
        "After confirming, switch to Pony Town. The process starts in {seconds} seconds. Press ESC or Stop to halt; session progress stays in memory while the app remains open.",
    ),
    "resume_from": ("Lanjut dari titik #{point}", "Resume from point #{point}"),
    "from_start": ("Mulai dari awal", "Start from the beginning"),
    "dlg_exit_title": ("Keluar?", "Exit?"),
    "dlg_exit_body": ("Penempatan masih berlangsung. Hentikan dan keluar?", "Placement is still running. Stop and exit?"),
    "countdown": ("Siapkan Pony Town, mulai dalam {seconds} detik. Tekan ESC untuk batal.", "Get Pony Town ready, starting in {seconds} s. Press ESC to cancel."),
    "placing": ("Menempatkan item. Jangan gerakkan mouse.", "Placing items. Do not move the mouse."),
    "run_cancelled": ("Penempatan dibatalkan sebelum klik dikirim.", "Placement canceled before any click was sent."),
    "paused": ("Dijeda. Tekan Lanjut untuk meneruskan atau Berhenti untuk berhenti.", "Paused. Press Resume to continue or Stop to stop."),
    "resumed": ("Dilanjutkan. Jangan gerakkan mouse.", "Resumed. Do not move the mouse."),
    "stopping": ("Meminta proses berhenti...", "Requesting stop..."),
    "esc_stop": ("ESC ditekan, menghentikan penempatan...", "ESC pressed, stopping placement..."),
    "finish_stopped_after": ("Dihentikan setelah titik #{point}. {sent} klik dikirim pada proses ini. Progres sesi tersimpan; lanjutkan tanpa mengulang titik yang sudah dicoba.", "Stopped after point #{point}. {sent} clicks sent in this run. Session progress is kept; continue without repeating attempted points."),
    "finish_stopped_before": ("Dihentikan sebelum titik pertama. Tidak ada klik yang dikirim.", "Stopped before the first point. No clicks were sent."),
    "finish_done": ("Selesai mengirim {sent} klik pada proses ini. Klik terkirim bukan konfirmasi bahwa semua item terpasang.", "Finished sending {sent} clicks in this run. Sent clicks do not confirm that every item was placed."),
    "finish_error": ("Proses terhenti karena error: {error}. Progres sebelumnya tetap di memori; periksa titik terakhir.", "The process stopped because of an error: {error}. Earlier progress is kept in memory; check the last point."),
    "warn_keyboard": ("Peringatan: tombol ESC global tidak aktif ({error}). Gunakan tombol Berhenti.", "Warning: global ESC key is inactive ({error}). Use the Stop button."),
    "missing_chars": ("{count} karakter tidak didukung ditampilkan sebagai ?", "{count} unsupported characters shown as ?"),
    "warn_pillow": ("Pillow belum terpasang: hanya karakter dasar yang didukung. Jalankan START.bat untuk memasangnya.", "Pillow is not installed: only basic characters are supported. Run START.bat to install it."),
    "warn_mouse": ("Peringatan: pelacakan kursor global tidak aktif ({error}).", "Warning: global cursor tracking is inactive ({error})."),
}


def clamp(value, low, high):
    return max(low, min(high, value))


@dataclass(frozen=True)
class Bitmap:
    points: frozenset
    width: int
    height: int
    char_height: int
    line_gap: int
    line_count: int
    font: str
    missing: int
    outline: bool


@dataclass(frozen=True)
class Pattern:
    bitmap: Bitmap
    points: frozenset
    width: int
    height: int
    res_x: float
    res_y: float
    available: int
    mode: str
    capped: bool

    @property
    def count(self):
        return len(self.points)

    @property
    def resolution(self):
        return (self.res_x + self.res_y) / 2.0

    @cached_property
    def ordered(self):
        return sorted(self.points, key=lambda point: (point[1], point[0]))


class PatternError(Exception):
    def __init__(self, key, **params):
        super().__init__(key)
        self.key = key
        self.params = params


@dataclass(frozen=True)
class Glyph:
    rows: tuple
    top: int
    width: int


def discover_fonts():
    if IS_WINDOWS:
        base = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        paths = [os.path.join(base, name) for name in WINDOWS_FONTS]
    else:
        roots = (
            "/usr/share/fonts", "/usr/local/share/fonts", "/Library/Fonts", "/System/Library/Fonts",
            os.path.expanduser("~/.fonts"), os.path.expanduser("~/Library/Fonts"),
        )
        paths = [
            os.path.join(folder, name)
            for root in roots
            for folder, _, names in os.walk(root)
            for name in names
            if name.lower().endswith((".ttf", ".otf", ".ttc"))
        ]
        preferred = ("dejavusans.", "cjk", "wqy", "notosans-regular")
        paths.sort(key=lambda path: (not any(tag in os.path.basename(path).lower() for tag in preferred), path))
    return [path for path in paths if os.path.isfile(path)]


class FontEntry:
    def __init__(self, path):
        self.path = path
        self._sizes = {}
        self.probe = self.at(48)
        self.notdef = self._sample("\U0010ffff")
        box = self.at(100).getbbox("H", anchor="ls")
        self.cap_ratio = (box[3] - box[1]) / 100.0 if box[3] > box[1] else 0.7

    def at(self, size):
        if size not in self._sizes:
            self._sizes[size] = ImageFont.truetype(self.path, size)
        return self._sizes[size]

    def _sample(self, char):
        image = Image.new("L", (96, 96), 0)
        ImageDraw.Draw(image).text((16, 72), char, font=self.probe, fill=255, anchor="ls")
        return image.tobytes() if image.getbbox() else None

    def covers(self, char):
        sample = self._sample(char)
        return sample is not None and sample != self.notdef


def render_glyph(entry, char, cap):
    scale = SUPERSAMPLE
    try:
        font = entry.at(max(8, round(cap * scale / entry.cap_ratio)))
        left, top, right, bottom = font.getbbox(char, anchor="ls")
        if right <= left or bottom <= top:
            return None
        col0, col1 = math.floor(left / scale), math.ceil(right / scale)
        row0, row1 = math.floor(top / scale) + cap, math.ceil(bottom / scale) + cap
        image = Image.new("L", ((col1 - col0) * scale, (row1 - row0) * scale), 0)
        ImageDraw.Draw(image).text((-col0 * scale, (cap - row0) * scale), char, font=font, fill=255, anchor="ls")
        small = image.resize((col1 - col0, row1 - row0), RESAMPLE_BOX)
    except Exception:
        return None
    pixels = small.load()
    cells = None
    for threshold in (INK_THRESHOLD, 0.2):
        limit = 255 * threshold
        grid = [[1 if pixels[x, y] >= limit else 0 for x in range(small.width)] for y in range(small.height)]
        if any(any(row) for row in grid):
            cells = grid
            break
    if cells is None:
        return None
    ys = [y for y, row in enumerate(cells) if any(row)]
    xs = [x for row in cells for x, value in enumerate(row) if value]
    x0, x1, y0, y1 = min(xs), max(xs), ys[0], ys[-1]
    rows = tuple("".join(str(value) for value in cells[y][x0:x1 + 1]) for y in range(y0, y1 + 1))
    return Glyph(rows, row0 + y0, x1 - x0 + 1)


class GlyphLibrary:
    def __init__(self):
        self._cache = {}
        self._entries = {}
        self._paths = None

    def _entry(self, path):
        if path not in self._entries:
            try:
                self._entries[path] = FontEntry(path)
            except Exception:
                self._entries[path] = None
        return self._entries[path]

    def lookup(self, char, font_key):
        table = FONTS[font_key]
        if char in table:
            rows = table[char]
            return Glyph(rows, 0, len(rows[0]))
        cap = len(table["A"])
        key = (char, cap)
        if key not in self._cache:
            self._cache[key] = self._rasterize(char, cap)
        return self._cache[key]

    def _rasterize(self, char, cap):
        if ImageFont is None:
            return None
        if self._paths is None:
            self._paths = discover_fonts()
        for path in self._paths:
            entry = self._entry(path)
            if entry is None or not entry.covers(char):
                continue
            glyph = render_glyph(entry, char, cap)
            if glyph is not None:
                return glyph
        return None


LIBRARY = GlyphLibrary()


def normalize_text(text):
    text = unicodedata.normalize("NFKC", text).translate(TYPOGRAPHY).replace("\t", "    ")
    return "".join(char for char in text if char.isspace() or unicodedata.category(char) not in IGNORED_CATEGORIES)


def build_bitmap(text, font_key, line_gap, align, outline=False):
    table = FONTS[font_key]
    cap = len(table["A"])
    space_width = 3 if len(table["A"][0]) == 5 else 2

    def lookup(char):
        return LIBRARY.lookup(char, font_key)

    lines = normalize_text(text).splitlines() or [""]
    placed = []
    widths = []
    missing = 0
    for line in lines:
        x = 0
        items = []
        for char in line:
            if char.isspace():
                x += space_width
                continue
            upper = char.upper()
            chars = upper if upper != char and all(lookup(c) is not None for c in upper) else char
            for item in chars:
                glyph = lookup(item)
                if glyph is None:
                    missing += 1
                    glyph = lookup("?")
                items.append((x, glyph))
                x += glyph.width + 1
        placed.append(items)
        widths.append(max(0, x - 1))
    glyphs = [glyph for items in placed for _, glyph in items]
    top = min([0] + [glyph.top for glyph in glyphs])
    bottom = max([cap] + [glyph.top + len(glyph.rows) for glyph in glyphs])
    line_height = bottom - top
    max_width = max(widths)
    points = set()
    for index, items in enumerate(placed):
        if align == ALIGN_CENTER:
            shift = (max_width - widths[index]) // 2
        elif align == ALIGN_RIGHT:
            shift = max_width - widths[index]
        else:
            shift = 0
        base_y = index * (line_height + line_gap) - top
        for x, glyph in items:
            for gy, row in enumerate(glyph.rows):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        points.add((x + gx + shift, base_y + glyph.top + gy))
    height = len(lines) * line_height + (len(lines) - 1) * line_gap
    return Bitmap(frozenset(points), max_width, height, line_height, line_gap, len(lines), font_key, missing, outline)


def axis_span(cell, resolution, total):
    start = max(0, math.ceil(cell * resolution - 0.5 - EPSILON))
    end = min(total, math.ceil((cell + 1) * resolution - 0.5 - EPSILON))
    return start, max(start, end)


def expand(bitmap, res_x, res_y):
    res_x = max(1.0, res_x)
    res_y = max(1.0, res_y)
    char_height = bitmap.char_height
    width = max(1, math.ceil(bitmap.width * res_x - EPSILON))
    glyph_height = max(1, math.ceil(char_height * res_y - EPSILON))
    line_step = max(glyph_height, math.ceil((char_height + bitmap.line_gap) * res_y - EPSILON))
    height = max(1, (max(1, bitmap.line_count) - 1) * line_step + glyph_height)
    stride = max(1, char_height + bitmap.line_gap)
    cells = bitmap.points
    rects = []
    for bx, by in cells:
        line, local_y = divmod(by, stride)
        x0, x1 = axis_span(bx, res_x, width)
        y0, y1 = axis_span(local_y, res_y, glyph_height)
        base_y = line * line_step
        rects.append((bx, by, x0, x1, base_y + y0, base_y + y1))
    if not bitmap.outline:
        points = {(x, y) for _, _, x0, x1, y0, y1 in rects for x in range(x0, x1) for y in range(y0, y1)}
        return points, width, height
    col_of = {}
    row_of = {}
    for bx, by, x0, x1, y0, y1 in rects:
        for x in range(x0, x1):
            col_of[x] = bx
        for y in range(y0, y1):
            row_of[y] = by

    def filled(x, y):
        return (col_of.get(x), row_of.get(y)) in cells

    points = set()
    for _, _, x0, x1, y0, y1 in rects:
        for y in range(y0, y1):
            xs = range(x0, x1) if y in (y0, y1 - 1) else (x0, x1 - 1)
            for x in xs:
                if not (filled(x - 1, y) and filled(x + 1, y) and filled(x, y - 1) and filled(x, y + 1)):
                    points.add((x, y))
    return points, width, height


def count_cells(bitmap, res_x, res_y):
    return len(expand(bitmap, res_x, res_y)[0])


def max_uniform_resolution(bitmap, available):
    base = max(1, count_cells(bitmap, 1.0, 1.0))
    if available <= base:
        return 1.0
    growth = available / base if bitmap.outline else math.sqrt(available / base)
    low, high = 1.0, max(2.0, min(growth + 2.0, 400.0))
    for _ in range(38):
        mid = (low + high) / 2.0
        if count_cells(bitmap, mid, mid) <= available:
            low = mid
        else:
            high = mid
    return low


def cap_resolution(bitmap, available, res_x, res_y):
    if count_cells(bitmap, res_x, res_y) <= available:
        return res_x, res_y, False
    if count_cells(bitmap, res_x, 1.0) <= available:
        low, high = 1.0, res_y
        for _ in range(40):
            mid = (low + high) / 2.0
            if count_cells(bitmap, res_x, mid) <= available:
                low = mid
            else:
                high = mid
        res_y = low
    else:
        target_x, target_y = res_x, res_y
        low, high = 0.0, 1.0
        for _ in range(40):
            factor = (low + high) / 2.0
            if count_cells(bitmap, 1.0 + (target_x - 1.0) * factor, 1.0 + (target_y - 1.0) * factor) <= available:
                low = factor
            else:
                high = factor
        res_x = 1.0 + (target_x - 1.0) * low
        res_y = 1.0 + (target_y - 1.0) * low
    while count_cells(bitmap, res_x, res_y) > available and res_y > 1.0:
        res_y = max(1.0, res_y - 0.001)
    while count_cells(bitmap, res_x, res_y) > available and (res_x > 1.0 or res_y > 1.0):
        res_x = max(1.0, res_x - 0.001)
        res_y = max(1.0, res_y - 0.001)
    return res_x, res_y, True


def fit_pattern(text, available, line_gap, align, mode, res_x=None, res_y=None, outline=False):
    if available < 1:
        raise PatternError("err_no_items")
    if not text.strip():
        raise PatternError("err_no_text")
    visible = sum(1 for char in text if not char.isspace())
    if visible > available:
        raise PatternError("err_too_big", available=available, needed=visible)
    bitmap = build_bitmap(text, FONT_DETAILED, line_gap, align, outline)
    if not bitmap.points:
        raise PatternError("err_no_text")
    if count_cells(bitmap, 1.0, 1.0) > available:
        compact = build_bitmap(text, FONT_COMPACT, line_gap, align, outline)
        needed = count_cells(compact, 1.0, 1.0)
        if needed > available:
            raise PatternError("err_too_big", available=available, needed=needed)
        bitmap = compact
    if res_x is None:
        res_x = max_uniform_resolution(bitmap, available) if mode == MODE_MAXIMUM else 1.0
    if res_y is None:
        res_y = res_x
    res_x, res_y, capped = cap_resolution(bitmap, available, max(1.0, res_x), max(1.0, res_y))
    points, width, height = expand(bitmap, res_x, res_y)
    return Pattern(bitmap, frozenset(points), width, height, res_x, res_y, available, mode, capped)


def resample_axis(pattern, axis, requested):
    bitmap = pattern.bitmap
    available = pattern.available
    res_x, res_y = pattern.res_x, pattern.res_y
    current = res_y if axis == "y" else res_x

    def count_with(value):
        return count_cells(bitmap, value if axis == "x" else res_x, value if axis == "y" else res_y)

    desired = max(1.0, requested)
    actual, capped = desired, False
    if desired > current and count_with(desired) > available:
        low, high = current, desired
        for _ in range(40):
            mid = (low + high) / 2.0
            if count_with(mid) <= available:
                low = mid
            else:
                high = mid
        actual, capped = low, True
    while count_with(actual) > available and actual > 1.0:
        actual, capped = max(1.0, actual - 0.001), True
    if axis == "x":
        res_x = actual
    else:
        res_y = actual
    points, width, height = expand(bitmap, res_x, res_y)
    return replace(pattern, points=frozenset(points), width=width, height=height, res_x=res_x, res_y=res_y, capped=capped)


def send_click(x, y):
    pyautogui.moveTo(x, y, duration=0)
    time.sleep(MOVE_SETTLE)
    pyautogui.mouseDown(button="left")
    try:
        time.sleep(PRESS_HOLD)
    finally:
        failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        try:
            pyautogui.mouseUp(button="left")
        finally:
            pyautogui.FAILSAFE = failsafe
    time.sleep(RELEASE_SETTLE)


GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000
LWA_COLORKEY = 0x00000001
LWA_ALPHA = 0x00000002
SWP_FLAGS = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020


def native_window(widget):
    handle = widget.winfo_id()
    return ctypes.windll.user32.GetAncestor(handle, 2) or handle


def tint_titlebar(window):
    if not IS_WINDOWS:
        return
    try:
        handle = native_window(window)
        dwm = ctypes.windll.dwmapi
        for attribute, value in ((20, 1), (19, 1), (35, 0x0A0A0A), (36, 0xF2F2F2), (34, 0x262626)):
            data = ctypes.c_int(value)
            dwm.DwmSetWindowAttribute(handle, attribute, ctypes.byref(data), ctypes.sizeof(data))
    except Exception:
        pass


SCALE = 1.0


def dp(value):
    return int(round(value * SCALE))


class Fonts:
    ui = "Helvetica"
    semibold = None
    mono = "Courier"

    @classmethod
    def resolve(cls, root):
        families = set(tkfont.families(root))
        cls.ui = next((n for n in ("Segoe UI Variable Text", "Segoe UI", "Inter", "Noto Sans", "DejaVu Sans") if n in families), cls.ui)
        cls.semibold = next((n for n in ("Segoe UI Variable Text Semibold", "Segoe UI Semibold") if n in families), None)
        cls.mono = next((n for n in ("Cascadia Mono", "Consolas", "DejaVu Sans Mono", "Courier New") if n in families), cls.mono)


def ui_font(size, bold=False):
    if bold:
        return (Fonts.semibold, size) if Fonts.semibold else (Fonts.ui, size, "bold")
    return (Fonts.ui, size)


def setup_metrics(root):
    global SCALE
    SCALE = max(1.0, root.winfo_fpixels("1i") / 96.0)
    Fonts.resolve(root)


def mix(first, second, ratio):
    a = [int(first[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(second[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * ratio) for x, y in zip(a, b))


def round_rect(canvas, x1, y1, x2, y2, radius, **options):
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **options)


def draw_align_icon(canvas, kind, cx, cy, color):
    widths = (dp(14), dp(9), dp(14), dp(6))
    half = dp(7)
    step = dp(3.5)
    for index, width in enumerate(widths):
        y = cy + (index - 1.5) * step
        if kind == ALIGN_LEFT:
            x0 = cx - half
        elif kind == ALIGN_RIGHT:
            x0 = cx + half - width
        else:
            x0 = cx - width / 2
        canvas.create_line(x0, y, x0 + width, y, fill=color, width=1)


def draw_double_arrow(canvas, cx, cy, horizontal, color):
    reach, head, flare, shaft = dp(9), dp(5), dp(4), dp(1)
    if horizontal:
        canvas.create_rectangle(cx - reach + head - 1, cy - shaft, cx + reach - head + 1, cy + shaft + 1, fill=color, outline="")
        canvas.create_polygon(cx - reach, cy, cx - reach + head, cy - flare, cx - reach + head, cy + flare + 1, fill=color, outline="")
        canvas.create_polygon(cx + reach, cy, cx + reach - head, cy - flare, cx + reach - head, cy + flare + 1, fill=color, outline="")
    else:
        canvas.create_rectangle(cx - shaft, cy - reach + head - 1, cx + shaft + 1, cy + reach - head + 1, fill=color, outline="")
        canvas.create_polygon(cx, cy - reach, cx - flare, cy - reach + head, cx + flare + 1, cy - reach + head, fill=color, outline="")
        canvas.create_polygon(cx, cy + reach, cx - flare, cy + reach - head, cx + flare + 1, cy + reach - head, fill=color, outline="")


def rule(parent):
    return tk.Frame(parent, bg=LINE, height=1)


class Button(tk.Canvas):
    STYLES = {
        "primary": {
            "fill": FG, "hover": "#ffffff", "press": "#c8c8c8", "text": INK, "hot_text": INK, "border": FG,
            "off_fill": "#232323", "off_text": "#6a6a6a", "off_border": "#232323",
        },
        "secondary": {
            "fill": RAISED, "hover": HOVER, "press": PRESSED, "text": FG, "hot_text": FG, "border": LINE_STRONG,
            "off_fill": None, "off_text": FAINT, "off_border": LINE,
        },
        "ghost": {
            "fill": None, "hover": HOVER, "press": PRESSED, "text": MUTED, "hot_text": FG, "border": None,
            "off_fill": None, "off_text": FAINT, "off_border": None,
        },
    }

    def __init__(self, master, text, command, kind="secondary", backdrop=BG, height=36, size=10, padx=18, width=None):
        self.font = tkfont.Font(root=master, font=ui_font(size, True))
        self.padx = dp(padx)
        self.fixed_width = dp(width) if width else None
        self.backdrop = backdrop
        super().__init__(
            master, width=self.fixed_width or self.font.measure(text) + 2 * self.padx, height=dp(height),
            bg=backdrop, highlightthickness=0, bd=0, takefocus=1, cursor="hand2",
        )
        self.text = text
        self.command = command
        self.enabled = True
        self._down = False
        self._hot = False
        self._focused = False
        self._job = None
        self._steps = 0
        self.set_kind(kind)
        self.bind("<Configure>", lambda _e: self._paint())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<FocusIn>", lambda _e: self._focus(True))
        self.bind("<FocusOut>", lambda _e: self._focus(False))
        self.bind("<Return>", lambda _e: self._invoke())
        self.bind("<space>", lambda _e: self._invoke())

    def set_kind(self, kind):
        style = dict(self.STYLES[kind])
        for key, value in style.items():
            if value is None:
                style[key] = self.backdrop
        self.style = style
        self._fill = style["fill"]
        self._goal = style["fill"]
        self._paint()

    def set_text(self, text):
        self.text = text
        if self.fixed_width is None:
            self.configure(width=self.font.measure(text) + 2 * self.padx)
        self._paint()

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self._down = False
        self._hot = False
        self._fill = self._goal = self.style["fill"]
        self.configure(cursor="hand2" if self.enabled else "arrow")
        self._paint()

    def _invoke(self):
        if self.enabled:
            self.command()

    def _focus(self, focused):
        self._focused = focused
        self._paint()

    def _set_goal(self, color):
        self._goal = color
        self._steps = 0
        if self._job is None:
            self._job = self.after(0, self._fade)

    def _fade(self):
        self._job = None
        if not self.winfo_exists():
            return
        self._steps += 1
        self._fill = self._goal if self._steps >= 5 else mix(self._fill, self._goal, 0.5)
        self._paint()
        if self._fill != self._goal:
            self._job = self.after(16, self._fade)

    def _enter(self, _event):
        if self.enabled:
            self._hot = True
            self._set_goal(self.style["press"] if self._down else self.style["hover"])

    def _leave(self, _event):
        self._hot = False
        self._down = False
        if self.enabled:
            self._set_goal(self.style["fill"])

    def _press(self, _event):
        if self.enabled:
            self._down = True
            self._set_goal(self.style["press"])

    def _release(self, event):
        was_down, self._down = self._down, False
        if not self.enabled or not was_down:
            return
        inside = 0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height()
        self._set_goal(self.style["hover"] if inside else self.style["fill"])
        if inside:
            self.command()

    def _paint(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if width < 8 or height < 8:
            return
        style = self.style
        fill = self._fill if self.enabled else style["off_fill"]
        border = style["border"] if self.enabled else style["off_border"]
        if self._focused:
            border = FG
        round_rect(self, 1, 1, width - 2, height - 2, dp(7), fill=fill, outline=border)
        if not self.enabled:
            color = style["off_text"]
        else:
            color = style["hot_text"] if self._hot else style["text"]
        self.create_text(width / 2, height / 2, text=self.text, font=self.font, fill=color)


class Segmented(tk.Canvas):
    def __init__(self, master, options, value, command, backdrop=BG, height=34, width=None):
        extra = {"width": width} if width else {}
        super().__init__(
            master, height=dp(height), bg=backdrop, highlightthickness=0, bd=0,
            takefocus=1, cursor="hand2", **extra,
        )
        self.values = [item[0] for item in options]
        self.labels = [item[1] for item in options]
        self.value = value
        self.command = command
        self.enabled = True
        self._hover = None
        self._focused = False
        self.font = tkfont.Font(root=master, font=ui_font(9))
        self.bind("<Configure>", lambda _e: self._paint())
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonPress-1>", self._click)
        self.bind("<FocusIn>", lambda _e: self._focus(True))
        self.bind("<FocusOut>", lambda _e: self._focus(False))
        self.bind("<Left>", lambda _e: self._shift(-1))
        self.bind("<Right>", lambda _e: self._shift(1))

    def set_labels(self, labels):
        self.labels = list(labels)
        self._paint()

    def set(self, value):
        self.value = value
        self._paint()

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self.configure(cursor="hand2" if self.enabled else "arrow")
        self._paint()

    def _focus(self, focused):
        self._focused = focused
        self._paint()

    def _index_at(self, x):
        inset = dp(3)
        segment = max(1.0, (self.winfo_width() - 2 * inset) / len(self.values))
        return clamp(int((x - inset) / segment), 0, len(self.values) - 1)

    def _motion(self, event):
        index = self._index_at(event.x) if self.enabled else None
        if index != self._hover:
            self._hover = index
            self._paint()

    def _leave(self, _event):
        self._hover = None
        self._paint()

    def _click(self, event):
        if self.enabled:
            self._select(self.values[self._index_at(event.x)])

    def _shift(self, delta):
        if self.enabled:
            index = clamp(self.values.index(self.value) + delta, 0, len(self.values) - 1)
            self._select(self.values[index])

    def _select(self, value):
        if value != self.value:
            self.value = value
            self._paint()
            self.command(value)

    def _paint(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if width < 8 or height < 8:
            return
        inset = dp(3)
        radius = dp(7)
        round_rect(self, 1, 1, width - 2, height - 2, radius, fill="#121212", outline=FG if self._focused else LINE)
        segment = (width - 2 * inset) / len(self.values)
        for index, (value, label) in enumerate(zip(self.values, self.labels)):
            left = inset + index * segment
            selected = value == self.value
            if selected:
                round_rect(self, left + 1, inset + 1, left + segment - 1, height - inset - 2, radius - dp(2), fill=PRESSED, outline=LINE_STRONG)
            if not self.enabled:
                color = FAINT
            elif selected or index == self._hover:
                color = FG
            else:
                color = MUTED
            cx, cy = left + segment / 2, height / 2
            if label.startswith("icon:"):
                draw_align_icon(self, label[5:], cx, cy, color)
            else:
                self.create_text(cx, cy, text=label, font=self.font, fill=color)


class Stepper(tk.Canvas):
    def __init__(self, master, minimum, maximum, value, command, backdrop=BG, height=34):
        super().__init__(master, width=dp(96), height=dp(height), bg=backdrop, highlightthickness=0, bd=0)
        self.minimum = minimum
        self.maximum = maximum
        self.command = command
        self.enabled = True
        self._value = clamp(value, minimum, maximum)
        self._quiet = False
        self._focused = False
        self._hover = None
        self._repeat = None
        self.var = tk.StringVar(master=self, value=str(self._value))
        self.entry = tk.Entry(
            self, textvariable=self.var, bd=0, highlightthickness=0, relief="flat", justify="center",
            bg=RAISED, fg=FG, insertbackground=FG, selectbackground="#444444", selectforeground=FG,
            disabledbackground=RAISED, disabledforeground=FAINT, font=ui_font(10),
            validate="key", validatecommand=(self.register(self._accept), "%P"),
        )
        self._window = self.create_window(0, 0, window=self.entry)
        self.var.trace_add("write", self._edited)
        self.entry.bind("<FocusIn>", lambda _e: self._focus(True))
        self.entry.bind("<FocusOut>", self._commit)
        self.entry.bind("<Return>", self._commit)
        self.entry.bind("<Up>", lambda _e: self.step(1))
        self.entry.bind("<Down>", lambda _e: self.step(-1))
        self.bind("<Configure>", lambda _e: self._paint())
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._stop_repeat)

    def get(self):
        return self._value

    def set(self, value):
        self._write(clamp(int(value), self.minimum, self.maximum))

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self.entry.configure(state="normal" if self.enabled else "disabled")
        self._stop_repeat()
        self._paint()

    def step(self, delta):
        if not self.enabled:
            return "break"
        value = clamp(self._value + delta, self.minimum, self.maximum)
        if value != self._value:
            self._write(value)
            self.command()
        return "break"

    def _accept(self, proposed):
        pattern = r"-?\d{0,5}" if self.minimum < 0 else r"\d{0,5}"
        return re.fullmatch(pattern, proposed) is not None

    def _write(self, value):
        self._quiet = True
        self._value = value
        self.var.set(str(value))
        self._quiet = False

    def _edited(self, *_):
        if self._quiet:
            return
        try:
            parsed = int(self.var.get())
        except ValueError:
            return
        value = clamp(parsed, self.minimum, self.maximum)
        if value != self._value:
            self._value = value
            self.command()

    def _commit(self, _event=None):
        self._write(self._value)
        self._focus(False)

    def _focus(self, focused):
        self._focused = focused
        self._paint()

    def _zone(self, x):
        width, zone = self.winfo_width(), self.winfo_height()
        if x < zone:
            return -1
        if x > width - zone:
            return 1
        return 0

    def _motion(self, event):
        hover = self._zone(event.x) or None
        if hover != self._hover:
            self._hover = hover
            self._paint()

    def _leave(self, _event):
        self._hover = None
        self._paint()

    def _press(self, event):
        direction = self._zone(event.x)
        if direction and self.enabled:
            self.entry.focus_set()
            self.step(direction)
            self._repeat = self.after(380, self._auto_repeat, direction)

    def _auto_repeat(self, direction):
        self.step(direction)
        self._repeat = self.after(60, self._auto_repeat, direction)

    def _stop_repeat(self, _event=None):
        if self._repeat is not None:
            self.after_cancel(self._repeat)
            self._repeat = None

    def _paint(self):
        self.delete("frame")
        width, height = self.winfo_width(), self.winfo_height()
        if width < 8 or height < 8:
            return
        round_rect(self, 1, 1, width - 2, height - 2, dp(7), fill=RAISED, outline=LINE_STRONG if self._focused else LINE, tags="frame")
        arm = dp(4)
        for direction, cx in ((-1, height / 2), (1, width - height / 2)):
            hot = self.enabled and self._hover == direction
            color = FG if hot else (MUTED if self.enabled else FAINT)
            self.create_line(cx - arm, height / 2, cx + arm + 1, height / 2, fill=color, tags="frame")
            if direction > 0:
                self.create_line(cx, height / 2 - arm, cx, height / 2 + arm + 1, fill=color, tags="frame")
        self.coords(self._window, width / 2, height / 2)
        self.itemconfigure(self._window, width=max(1, width - 2 * height), height=max(1, height - dp(10)))
        self.tag_lower("frame")


class TextArea(tk.Canvas):
    def __init__(self, master, command, backdrop=BG, height=92):
        super().__init__(master, height=dp(height), bg=backdrop, highlightthickness=0, bd=0)
        self.command = command
        self._focused = False
        self.text = tk.Text(
            self, wrap="word", bd=0, highlightthickness=0, relief="flat", bg=RAISED, fg=FG,
            insertbackground=FG, selectbackground="#444444", selectforeground=FG,
            font=(Fonts.mono, 11), padx=dp(4), pady=dp(2), undo=True,
        )
        self._window = self.create_window(0, 0, window=self.text, anchor="nw")
        self.bind("<Configure>", lambda _e: self._layout())
        self.text.bind("<FocusIn>", lambda _e: self._focus(True))
        self.text.bind("<FocusOut>", lambda _e: self._focus(False))
        self.text.bind("<<Modified>>", self._modified)

    def get(self):
        return self.text.get("1.0", "end-1c")

    def set(self, value):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        self.text.edit_reset()
        self.text.edit_modified(False)

    def set_enabled(self, enabled):
        self.text.configure(state="normal" if enabled else "disabled", fg=FG if enabled else FAINT)

    def _modified(self, _event):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self.command()

    def _focus(self, focused):
        self._focused = focused
        self._paint()

    def _layout(self):
        width, height = self.winfo_width(), self.winfo_height()
        pad_x, pad_y = dp(10), dp(8)
        self.coords(self._window, pad_x, pad_y)
        self.itemconfigure(self._window, width=max(1, width - 2 * pad_x), height=max(1, height - 2 * pad_y))
        self._paint()

    def _paint(self):
        self.delete("frame")
        width, height = self.winfo_width(), self.winfo_height()
        if width < 8 or height < 8:
            return
        round_rect(self, 1, 1, width - 2, height - 2, dp(8), fill=RAISED, outline=LINE_STRONG if self._focused else LINE, tags="frame")
        self.tag_lower("frame")


class Slider(tk.Canvas):
    def __init__(self, master, minimum, maximum, value, command, backdrop=BG, height=24):
        super().__init__(master, height=dp(height), bg=backdrop, highlightthickness=0, bd=0, takefocus=1, cursor="hand2")
        self.minimum = minimum
        self.maximum = maximum
        self.value = value
        self.command = command
        self.enabled = True
        self._hover = False
        self._focused = False
        self._dragging = False
        self.bind("<Configure>", lambda _e: self._paint())
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._drag_start)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", self._drag_end)
        self.bind("<FocusIn>", lambda _e: self._set_focus(True))
        self.bind("<FocusOut>", lambda _e: self._set_focus(False))
        self.bind("<Left>", lambda _e: self._select(self.value - 1))
        self.bind("<Right>", lambda _e: self._select(self.value + 1))

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self._paint()

    def _set_hover(self, hover):
        self._hover = hover
        self._paint()

    def _set_focus(self, focused):
        self._focused = focused
        self._paint()

    def _bounds(self):
        pad = dp(9)
        return pad, max(pad + 1, self.winfo_width() - pad)

    def _value_at(self, x):
        left, right = self._bounds()
        ratio = clamp((x - left) / (right - left), 0.0, 1.0)
        return int(round(self.minimum + ratio * (self.maximum - self.minimum)))

    def _select(self, value):
        value = clamp(value, self.minimum, self.maximum)
        if self.enabled and value != self.value:
            self.value = value
            self._paint()
            self.command(value)

    def _drag_start(self, event):
        self._dragging = True
        self._select(self._value_at(event.x))

    def _drag(self, event):
        if self._dragging:
            self._select(self._value_at(event.x))

    def _drag_end(self, _event):
        self._dragging = False
        self._paint()

    def _paint(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if width < 20:
            return
        left, right = self._bounds()
        y = height / 2
        ratio = (self.value - self.minimum) / (self.maximum - self.minimum)
        x = left + ratio * (right - left)
        stroke = max(2, dp(3))
        self.create_line(left, y, right, y, fill=LINE_STRONG, width=stroke, capstyle="round")
        self.create_line(left, y, x, y, fill=FG if self.enabled else FAINT, width=stroke, capstyle="round")
        radius = dp(8) if (self._hover or self._dragging) and self.enabled else dp(6)
        self.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=FG if self.enabled else FAINT, outline=BG, width=2 if self._focused else 0,
        )


class Switch(tk.Canvas):
    def __init__(self, master, value, command, backdrop=BG):
        super().__init__(master, width=dp(40), height=dp(22), bg=backdrop, highlightthickness=0, bd=0, takefocus=1, cursor="hand2")
        self.value = bool(value)
        self.command = command
        self.enabled = True
        self._focused = False
        self.bind("<Configure>", lambda _e: self._paint())
        self.bind("<ButtonPress-1>", lambda _e: self._toggle())
        self.bind("<space>", lambda _e: self._toggle())
        self.bind("<Return>", lambda _e: self._toggle())
        self.bind("<FocusIn>", lambda _e: self._focus(True))
        self.bind("<FocusOut>", lambda _e: self._focus(False))

    def set(self, value):
        self.value = bool(value)
        self._paint()

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self.configure(cursor="hand2" if self.enabled else "arrow")
        self._paint()

    def _focus(self, focused):
        self._focused = focused
        self._paint()

    def _toggle(self):
        if self.enabled:
            self.value = not self.value
            self._paint()
            self.command(self.value)

    def _paint(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if width < 16 or height < 10:
            return
        on = self.value
        if self.enabled:
            track, knob, border = (FG, INK, FG) if on else ("#141414", MUTED, LINE_STRONG)
        else:
            track, knob, border = ("#3a3a3a", "#6a6a6a", "#3a3a3a") if on else ("#101010", FAINT, LINE)
        if self._focused:
            border = FG
        round_rect(self, 1, 1, width - 2, height - 2, (height - 3) / 2, fill=track, outline=border)
        radius = (height - dp(10)) / 2
        cx = width - height / 2 if on else height / 2
        self.create_oval(cx - radius, height / 2 - radius, cx + radius, height / 2 + radius, fill=knob, outline="")


class BrandMark(tk.Canvas):
    def __init__(self, master, backdrop):
        cell, gap = dp(3), max(1, dp(1))
        rows = FONT_5X7["P"]
        width = len(rows[0]) * (cell + gap) - gap
        height = len(rows) * (cell + gap) - gap
        super().__init__(master, width=width, height=height, bg=backdrop, highlightthickness=0, bd=0)
        for y, row in enumerate(rows):
            for x, bit in enumerate(row):
                left, top = x * (cell + gap), y * (cell + gap)
                self.create_rectangle(left, top, left + cell, top + cell, fill=FG if bit == "1" else LINE, outline="")


class Dialog(tk.Toplevel):
    def __init__(self, app, title, message, buttons):
        super().__init__(app.root)
        self.withdraw()
        self.title(APP_NAME)
        self.configure(bg=SURFACE)
        self.resizable(False, False)
        self.transient(app.root)
        self.result = False
        self.default = buttons[-1][1]
        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=dp(26), pady=(dp(24), dp(18)))
        tk.Label(body, text=title, bg=SURFACE, fg=FG, font=ui_font(11, True), anchor="w").pack(fill="x")
        tk.Label(
            body, text=message, bg=SURFACE, fg=MUTED, font=ui_font(9), justify="left",
            anchor="w", wraplength=dp(400),
        ).pack(fill="x", pady=(dp(8), 0))
        row = tk.Frame(self, bg=SURFACE)
        row.pack(fill="x", padx=dp(26), pady=(0, dp(22)))
        for label, value, kind in reversed(buttons):
            Button(row, label, lambda v=value: self._close(v), kind, SURFACE, height=34, size=9, padx=20).pack(side="right", padx=(dp(8), 0))
        self.bind("<Return>", lambda _e: self._close(self.default))
        self.bind("<Escape>", lambda _e: self._close(False))
        self.protocol("WM_DELETE_WINDOW", lambda: self._close(False))
        self.update_idletasks()
        x = app.root.winfo_rootx() + (app.root.winfo_width() - self.winfo_reqwidth()) // 2
        y = app.root.winfo_rooty() + (app.root.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        tint_titlebar(self)
        self.attributes("-topmost", True)
        self.deiconify()

    def _close(self, value):
        self.result = value
        self.destroy()

    def run(self):
        try:
            self.wait_visibility()
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass
        self.wait_window(self)
        return self.result


class LiveText:
    def __init__(self, app, key="", **params):
        self.app = app
        self.var = tk.StringVar(master=app.root)
        app.live_texts.append(self)
        self.set(key, **params)

    def set(self, key, **params):
        self.key = key
        self.params = params
        self.refresh()

    def refresh(self):
        self.var.set(self.app.t(self.key, **self.params) if self.key else "")


class Overlay:
    COLOR_KEY = "#ff00ff"
    COLOR_KEY_REF = 0x00FF00FF
    MIN_PITCH = float(PITCH_RANGE[0])
    MAX_PITCH = float(PITCH_RANGE[1])

    def __init__(self, app, pattern):
        self.app = app
        self.pattern = pattern
        self.pitch_x = float(app.grid_x.get())
        self.pitch_y = float(app.grid_y.get())
        self.row_offset = float(app.row_offset.get())
        self.locked = False
        self.visible = True
        self.hover = None
        self.toolbar = None
        self.grips = {}
        self.top = None
        self._marker = None
        self._drag = None
        self.header = dp(34)
        self.padding = dp(22)
        self.gutter = dp(28)
        self.grip_size = dp(28)
        self.min_width = dp(400)
        try:
            self._build()
        except Exception:
            self.destroy()
            raise

    def _build(self):
        self.top = tk.Toplevel(self.app.root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        try:
            self.top.wm_attributes("-transparentcolor", self.COLOR_KEY)
        except tk.TclError:
            self.top.attributes("-alpha", OVERLAY_ALPHA)
        self.canvas = tk.Canvas(self.top, bg=self.COLOR_KEY, highlightthickness=0, bd=0, cursor="fleur")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", lambda e: self._press(e, "move"))
        self.canvas.bind("<B1-Motion>", self._motion)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.top.update_idletasks()
        self._fit()
        self.top.geometry(f"{self.width()}x{self.height()}+0+0")
        self.center()
        self._build_toolbar()
        self._build_grips()
        self._sync_children()
        self.refresh_texts()
        self.render()
        self._apply_style()

    def _build_toolbar(self):
        app = self.app
        self.toolbar = tk.Toplevel(app.root)
        self.toolbar.overrideredirect(True)
        self.toolbar.attributes("-topmost", True)
        self.toolbar.configure(bg=SURFACE)
        bar = tk.Frame(self.toolbar, bg=SURFACE)
        bar.pack(fill="both", expand=True, padx=dp(8))
        options = {"backdrop": SURFACE, "height": 26, "size": 9, "padx": 10}
        self.hide_button = Button(bar, "", app.hide_overlay, "ghost", **options)
        self.hide_button.pack(side="right", pady=dp(4))
        self.repair_button = Button(bar, "", app.toggle_repair, "secondary", **options)
        self.repair_button.pack(side="right", pady=dp(4), padx=(0, dp(6)))
        self.lock_button = Button(bar, "", app.toggle_lock, "secondary", **options)
        self.lock_button.pack(side="right", pady=dp(4), padx=(0, dp(6)))
        self.handle = tk.Canvas(bar, width=dp(8), height=dp(14), bg=SURFACE, highlightthickness=0, bd=0)
        for col in range(2):
            for row in range(3):
                left, top = col * dp(5), row * dp(5)
                self.handle.create_rectangle(left, top, left + dp(2), top + dp(2), fill=FAINT, outline="", tags="dot")
        self.handle.pack(side="left", padx=(dp(2), dp(8)))
        self.drag_label = tk.Label(bar, bg=SURFACE, fg=MUTED, font=ui_font(9), anchor="w")
        self.drag_label.pack(side="left", fill="both", expand=True)
        self.drag_widgets = (bar, self.handle, self.drag_label)
        for widget in self.drag_widgets:
            widget.bind("<ButtonPress-1>", lambda e: self._press(e, "move"))
            widget.bind("<B1-Motion>", self._motion)
            widget.bind("<ButtonRelease-1>", self._release)

    def _build_grips(self):
        size = self.grip_size
        inner = size - 2
        for axis in ("x", "y"):
            grip = tk.Toplevel(self.app.root)
            grip.overrideredirect(True)
            grip.attributes("-topmost", True)
            grip.configure(bg=FG)
            cursor = "sb_h_double_arrow" if axis == "x" else "sb_v_double_arrow"
            canvas = tk.Canvas(grip, width=inner, height=inner, bg=INK, highlightthickness=0, bd=0, cursor=cursor)
            canvas.pack(padx=1, pady=1)
            draw_double_arrow(canvas, inner / 2, inner / 2, axis == "x", FG)
            canvas.bind("<ButtonPress-1>", lambda e, a=axis: self._press(e, f"resize_{a}"))
            canvas.bind("<B1-Motion>", self._motion)
            canvas.bind("<ButtonRelease-1>", self._release)
            self.grips[axis] = grip

    def refresh_texts(self):
        t = self.app.t
        cursor = "arrow" if self.locked else "fleur"
        for widget in (*self.drag_widgets, self.canvas):
            widget.configure(cursor=cursor)
        self.handle.itemconfigure("dot", fill=LINE_STRONG if self.locked else FAINT)
        self.drag_label.configure(text=t("locked_label" if self.locked else "drag_to_move"))
        self.lock_button.set_text(t("unlock_short" if self.locked else "lock_short"))
        self.repair_button.set_text(t("repair_active_short" if self.app.repair_active else "repair_short"))
        self.repair_button.set_kind("primary" if self.app.repair_active else "secondary")
        self.hide_button.set_text(t("hide_short"))

    def set_busy(self, busy):
        for button in (self.lock_button, self.repair_button, self.hide_button):
            button.set_enabled(not busy)

    def _shift_range(self):
        span = self.row_offset * max(0, self.pattern.height - 1)
        return min(-span / 2, span / 2), max(-span / 2, span / 2)

    def _content_width(self):
        low, high = self._shift_range()
        return max(1, self.pattern.width) * self.pitch_x + (high - low)

    def width(self):
        return max(self.min_width, int(2 * (self.padding + self.gutter) + self._content_width()))

    def height(self):
        rows = max(1, self.pattern.height) * self.pitch_y
        return max(dp(70), int(self.header + self.padding + rows + self.gutter))

    def left(self):
        low, _ = self._shift_range()
        return (self.width() - self._content_width()) / 2.0 - low

    def top_edge(self):
        return self.header + self.padding

    def row_shift(self, row):
        return (row - (max(1, self.pattern.height) - 1) / 2.0) * self.row_offset

    def _bounds(self):
        low, high = self._shift_range()
        left, top = self.left(), self.top_edge()
        right = left + max(1, self.pattern.width) * self.pitch_x + high
        bottom = top + max(1, self.pattern.height) * self.pitch_y
        return left + low, top, right, bottom

    def _fit(self):
        screen_w, screen_h = self.top.winfo_screenwidth(), self.top.winfo_screenheight()
        pattern = self.pattern
        row_span = abs(self.row_offset) * max(0, pattern.height - 1)
        room_x = (screen_w - 2 * (self.padding + self.gutter) - dp(40) - row_span) / max(1, pattern.width)
        room_y = (screen_h - self.header - self.padding - self.gutter - dp(120)) / max(1, pattern.height)
        self.pitch_x = min(self.pitch_x, clamp(room_x, self.MIN_PITCH, self.MAX_PITCH))
        self.pitch_y = min(self.pitch_y, clamp(room_y, self.MIN_PITCH, self.MAX_PITCH))

    def _place(self, x=None, y=None):
        x = self.top.winfo_x() if x is None else x
        y = self.top.winfo_y() if y is None else y
        self.top.geometry(f"{self.width()}x{self.height()}+{int(x)}+{int(y)}")
        self.top.update_idletasks()
        self._sync_children()
        if self.app.repair_active:
            self.app.refresh_repair_targets()

    def center(self):
        screen_w, screen_h = self.top.winfo_screenwidth(), self.top.winfo_screenheight()
        self._place(max(10, (screen_w - self.width()) // 2), max(10, (screen_h - self.height()) // 2))

    def _sync_children(self):
        if self.toolbar is None or len(self.grips) < 2:
            return
        x, y = self.top.winfo_rootx(), self.top.winfo_rooty()
        width, height = self.width(), self.height()
        size = self.grip_size
        self.toolbar.geometry(f"{width}x{self.header}+{x}+{y}")
        self.grips["x"].geometry(f"{size}x{size}+{x + width - size - 2}+{y + self.header + 2}")
        self.grips["y"].geometry(f"{size}x{size}+{x + 2}+{y + height - size - 2}")

    def _apply_style(self):
        if not IS_WINDOWS:
            return
        try:
            user32 = ctypes.windll.user32
            handle = native_window(self.top)
            style = user32.GetWindowLongW(handle, GWL_EXSTYLE) | WS_EX_LAYERED | WS_EX_TOOLWINDOW
            if self.locked:
                style |= WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
            else:
                style &= ~(WS_EX_TRANSPARENT | WS_EX_NOACTIVATE)
            user32.SetWindowLongW(handle, GWL_EXSTYLE, style)
            user32.SetWindowPos(handle, 0, 0, 0, 0, 0, SWP_FLAGS)
            user32.SetLayeredWindowAttributes(handle, self.COLOR_KEY_REF, int(255 * OVERLAY_ALPHA), LWA_COLORKEY | LWA_ALPHA)
        except Exception:
            pass

    def set_pattern(self, pattern):
        self.pattern = pattern
        self.hover = None
        if not self.visible:
            return
        self._fit()
        self._place()
        self.render()
        self._apply_style()

    def adopt(self, pattern):
        self.pattern = pattern
        self.hover = None

    def set_grid(self, pitch_x=None, pitch_y=None, row_offset=None):
        if pitch_x is not None:
            self.pitch_x = float(pitch_x)
        if pitch_y is not None:
            self.pitch_y = float(pitch_y)
        if row_offset is not None:
            self.row_offset = float(row_offset)
        if self.visible:
            self._place()
            self.render()

    def set_locked(self, locked):
        self.locked = bool(locked)
        self._apply_style()
        self.refresh_texts()
        self.render()
        self.app.overlay_state_changed()

    def set_hover(self, index):
        self.hover = index
        if self._marker is None:
            return
        ordered = self.pattern.ordered
        if index is None or not 0 <= index < len(ordered):
            self.canvas.itemconfigure(self._marker, state="hidden")
            return
        col, row = ordered[index]
        cx = self.left() + (col + 0.5) * self.pitch_x + self.row_shift(row)
        cy = self.top_edge() + (row + 0.5) * self.pitch_y
        radius = max(4.0, (self.pitch_x + self.pitch_y) / 2.0 * 0.48)
        self.canvas.coords(self._marker, cx - radius, cy - radius, cx + radius, cy + radius)
        self.canvas.itemconfigure(self._marker, state="normal")

    def render(self):
        canvas = self.canvas
        canvas.delete("all")
        pattern = self.pattern
        left, top = self.left(), self.top_edge()
        x1, _, x2, y2 = self._bounds()
        canvas.create_rectangle(0, 0, self.width(), self.header, fill=SURFACE, outline="")
        canvas.create_rectangle(x1 - 2, top - 2, x2 + 2, y2 + 2, outline="#bdbdbd", width=1)
        if not self.locked and min(self.pitch_x, self.pitch_y) >= 10:
            cols, rows = max(1, pattern.width), max(1, pattern.height)
            for col in range(cols + 1):
                x = left + col * self.pitch_x
                canvas.create_line(x + self.row_shift(0), top, x + self.row_shift(rows - 1), top + rows * self.pitch_y, fill="#777777")
            for row in range(rows + 1):
                y = top + row * self.pitch_y
                shift = (row - (rows - 1) / 2.0) * self.row_offset
                canvas.create_line(left + shift, y, left + shift + cols * self.pitch_x, y, fill="#777777")
        dot = max(2.0, min(self.pitch_x, self.pitch_y) * 0.64)
        outline = "#161616" if dot >= 6 else ""
        for col, row in pattern.ordered:
            cx = left + (col + 0.5) * self.pitch_x + self.row_shift(row)
            cy = top + (row + 0.5) * self.pitch_y
            canvas.create_rectangle(cx - dot / 2, cy - dot / 2, cx + dot / 2, cy + dot / 2, fill="#f5f5f5", outline=outline)
        self._marker = canvas.create_oval(0, 0, 0, 0, outline=FG, width=2, state="hidden")
        self.set_hover(self.hover)

    def screen_points(self):
        x0, y0 = self.top.winfo_rootx(), self.top.winfo_rooty()
        left, top = self.left(), self.top_edge()
        return [
            (round(x0 + left + (col + 0.5) * self.pitch_x + self.row_shift(row)), round(y0 + top + (row + 0.5) * self.pitch_y))
            for col, row in self.pattern.ordered
        ]

    def _press(self, event, mode):
        if self.app.running or (self.locked and mode == "move"):
            return
        self._drag = (
            mode, event.x_root, event.y_root, self.top.winfo_x(), self.top.winfo_y(),
            self.pitch_x, self.pitch_y, self.pattern.res_x, self.pattern.res_y,
        )

    def _motion(self, event):
        if self._drag is None or self.app.running:
            return
        mode, start_x, start_y, origin_x, origin_y, pitch_x, pitch_y, res_x, res_y = self._drag
        dx, dy = event.x_root - start_x, event.y_root - start_y
        if mode == "move":
            self._place(origin_x + dx, origin_y + dy)
            return
        axis = "x" if mode == "resize_x" else "y"
        if self.app.mode == MODE_AUTO:
            bitmap = self.pattern.bitmap
            if axis == "x":
                requested = res_x + dx / max(1.0, max(1, bitmap.width) * pitch_x)
            else:
                requested = res_y + dy / max(1.0, max(1, bitmap.height) * pitch_y)
            self.app.resize_pattern(axis, max(1.0, requested))
            self.pitch_x, self.pitch_y = pitch_x, pitch_y
        elif axis == "x":
            self.pitch_x = clamp(pitch_x + dx / max(1, self.pattern.width), self.MIN_PITCH, self.MAX_PITCH)
        else:
            self.pitch_y = clamp(pitch_y + dy / max(1, self.pattern.height), self.MIN_PITCH, self.MAX_PITCH)
        self._place(origin_x, origin_y)
        self.render()

    def _release(self, _event):
        drag, self._drag = self._drag, None
        if drag and drag[0] != "move":
            self.app.sync_grid_fields()

    def show(self):
        self.visible = True
        self.top.deiconify()
        self._place()
        for window in (self.top, self.toolbar, *self.grips.values()):
            window.deiconify()
            window.attributes("-topmost", True)
        self._apply_style()
        self.render()

    def hide(self):
        self.visible = False
        for window in (self.top, self.toolbar, *self.grips.values()):
            window.withdraw()

    def destroy(self):
        for window in (self.toolbar, *self.grips.values(), self.top):
            if window is not None:
                try:
                    window.destroy()
                except tk.TclError:
                    pass


class App:
    def __init__(self, root):
        self.root = root
        self.lang = "ID"
        self.mode = MODE_AUTO
        self.align = ALIGN_LEFT
        self.outline = False
        self.live_texts = []
        self._bound = []
        self.inbox = queue.SimpleQueue()
        self.overlay = None
        self.pattern = None
        self.error = None
        self.pattern_signature = None
        self.attempted = set()
        self.next_index = 0
        self.run_signature = None
        self.targets = []
        self.running = False
        self.paused = False
        self.closing = False
        self.stop_event = threading.Event()
        self.resume_event = threading.Event()
        self.resume_event.set()
        self.worker = None
        self.mouse_pos = (0, 0)
        self.mouse_lock = threading.Lock()
        self.repair_active = False
        self.repair_targets = []
        self.repair_hover = None
        self.repair_since = None
        self.repair_tried = set()
        self.keyboard_listener = None
        self.mouse_listener = None
        self._wide = None
        self._scrollable = False

        root.withdraw()
        root.title(APP_NAME)
        root.configure(bg=BG)
        root.minsize(dp(560), dp(520))
        width = min(dp(1080), root.winfo_screenwidth() - dp(80))
        height = min(dp(860), root.winfo_screenheight() - dp(100))
        root.geometry(f"{width}x{height}+{(root.winfo_screenwidth() - width) // 2}+{max(10, (root.winfo_screenheight() - height) // 3)}")

        self.status = LiveText(self, "ready")
        self.progress = LiveText(self, "not_started")
        self._build()
        self.text_area.set(DEFAULT_TEXT)
        self.refresh_pattern()
        self.status.set("ready")
        self.progress.set("not_started")
        if Image is None:
            self.status.set("warn_pillow")

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind_all("<MouseWheel>", self._on_wheel)
        root.bind_all("<Button-4>", self._on_wheel)
        root.bind_all("<Button-5>", self._on_wheel)
        self._start_keyboard()
        self._start_mouse()
        root.after(TICK_MS, self._tick)
        self._reveal()

    def t(self, key, **params):
        text = STRINGS[key][0 if self.lang == "ID" else 1]
        return text.format(**params) if params else text

    def post(self, function, *args):
        self.inbox.put((function, args))

    def _bind(self, key, apply):
        self._bound.append((key, apply))
        apply(self.t(key))

    def label(self, parent, key, bg, fg, size=9, bold=False, **options):
        widget = tk.Label(parent, bg=bg, fg=fg, font=ui_font(size, bold), **options)
        self._bind(key, lambda text: widget.configure(text=text))
        return widget

    def button(self, parent, key, command, kind="secondary", **options):
        widget = Button(parent, self.t(key), command, kind, **options)
        self._bind(key, widget.set_text)
        return widget

    def _field(self, parent, column, key, minimum, maximum, value, command):
        cell = tk.Frame(parent, bg=BG)
        cell.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else dp(8), 0))
        parent.grid_columnconfigure(column, weight=1, uniform="field")
        self.label(cell, key, BG, MUTED, 8).pack(anchor="w", pady=(0, dp(5)))
        stepper = Stepper(cell, minimum, maximum, value, command)
        stepper.pack(fill="x")
        return stepper

    def _build(self):
        root = self.root
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=dp(24), pady=(dp(16), dp(14)))
        BrandMark(header, BG).pack(side="left", padx=(0, dp(14)))
        titles = tk.Frame(header, bg=BG)
        titles.pack(side="left")
        tk.Label(titles, text=APP_NAME, bg=BG, fg=FG, font=ui_font(14, True)).pack(anchor="w")
        self.label(titles, "subtitle", BG, MUTED).pack(anchor="w", pady=(dp(1), 0))
        self.language = Segmented(header, [("ID", "ID"), ("EN", "EN")], self.lang, self.set_language, height=30, width=dp(92))
        self.language.pack(side="right")
        rule(root).pack(fill="x")

        footer = tk.Frame(root, bg=BG)
        footer.pack(side="bottom", fill="x")
        rule(footer).pack(fill="x")
        bar = tk.Frame(footer, bg=BG)
        bar.pack(fill="x", padx=dp(24), pady=dp(9))
        self.credit_label = tk.Label(bar, text=CREDIT, bg=BG, fg=FAINT, font=ui_font(8))
        self.credit_label.pack(side="right")
        self.progress_label = tk.Label(bar, textvariable=self.progress.var, bg=BG, fg=MUTED, font=ui_font(8))
        self.progress_label.pack(side="right", padx=(dp(16), dp(16)))
        self.status_label = tk.Label(bar, textvariable=self.status.var, bg=BG, fg=FG, font=ui_font(8), anchor="w", justify="left")
        self.status_label.pack(side="left", fill="x", expand=True)
        footer.bind("<Configure>", self._on_footer)

        self.viewport = tk.Canvas(root, bg=BG, highlightthickness=0, bd=0, yscrollincrement=dp(24), yscrollcommand=self._on_scrolled)
        self.viewport.pack(fill="both", expand=True)
        self.scroll_hint = tk.Canvas(root, bg=BG, highlightthickness=0, bd=0)
        self.page = tk.Frame(self.viewport, bg=BG)
        self.page_window = self.viewport.create_window(0, 0, window=self.page, anchor="nw")
        self.viewport.bind("<Configure>", self._on_viewport)
        self.controls = tk.Frame(self.page, bg=BG)
        self.preview = tk.Frame(self.page, bg=BG)
        self.divider = tk.Frame(self.page, bg=LINE)
        self._build_controls()
        self._build_preview()

    def _build_controls(self):
        inner = tk.Frame(self.controls, bg=BG)
        inner.pack(fill="both", expand=True, padx=dp(24), pady=dp(20))
        self.label(inner, "text_label", BG, MUTED, 8).pack(anchor="w", pady=(0, dp(6)))
        self.text_area = TextArea(inner, self.refresh_pattern)
        self.text_area.pack(fill="x")
        self.label(inner, "text_hint", BG, FAINT, 8).pack(anchor="w", pady=(dp(6), dp(16)))

        row = tk.Frame(inner, bg=BG)
        row.pack(fill="x")
        self.limit = self._field(row, 0, "limit_total", 1, MAX_ITEMS, DEFAULT_LIMIT, self.refresh_pattern)
        self.used = self._field(row, 1, "already_placed", 0, MAX_ITEMS, 0, self.refresh_pattern)
        self.gap = self._field(row, 2, "line_gap", GAP_RANGE[0], GAP_RANGE[1], DEFAULT_GAP, self.refresh_pattern)

        self.label(inner, "grid_mode", BG, MUTED, 8).pack(anchor="w", pady=(dp(16), dp(5)))
        self.mode_seg = Segmented(
            inner,
            [(MODE_BALANCED, self.t("mode_balanced")), (MODE_AUTO, self.t("mode_auto")), (MODE_MAXIMUM, self.t("mode_maximum"))],
            self.mode, self.set_mode,
        )
        self.mode_seg.pack(fill="x")
        self.mode_help = tk.Label(inner, bg=BG, fg=FAINT, font=ui_font(8), anchor="w", justify="left", wraplength=dp(310))
        self.mode_help.pack(fill="x", pady=(dp(6), dp(14)))
        self._sync_mode_help()

        self.label(inner, "alignment", BG, MUTED, 8).pack(anchor="w", pady=(0, dp(5)))
        self.align_seg = Segmented(
            inner,
            [(ALIGN_LEFT, f"icon:{ALIGN_LEFT}"), (ALIGN_CENTER, f"icon:{ALIGN_CENTER}"), (ALIGN_RIGHT, f"icon:{ALIGN_RIGHT}")],
            self.align, self.set_align,
        )
        self.align_seg.pack(fill="x")

        row = tk.Frame(inner, bg=BG)
        row.pack(fill="x", pady=(dp(16), 0))
        self.label(row, "outline", BG, FG, 9).pack(side="left")
        self.outline_switch = Switch(row, False, self.set_outline)
        self.outline_switch.pack(side="right")
        self.label(inner, "outline_help", BG, FAINT, 8, wraplength=dp(310), justify="left", anchor="w").pack(fill="x", pady=(dp(6), 0))

        rule(inner).pack(fill="x", pady=dp(20))
        head = tk.Frame(inner, bg=BG)
        head.pack(fill="x", pady=(0, dp(10)))
        self.label(head, "grid_section", BG, FG, 10, True).pack(side="left")
        self.reset_button = self.button(head, "reset", self.reset_layout, "ghost", height=26, size=9, padx=10)
        self.reset_button.pack(side="right")

        row = tk.Frame(inner, bg=BG)
        row.pack(fill="x")
        self.grid_x = self._field(row, 0, "grid_x", *PITCH_RANGE, DEFAULT_PITCH, lambda: self.apply_grid(pitch_x=self.grid_x.get()))
        self.grid_y = self._field(row, 1, "grid_y", *PITCH_RANGE, DEFAULT_PITCH, lambda: self.apply_grid(pitch_y=self.grid_y.get()))
        self.row_offset = self._field(row, 2, "row_offset", *OFFSET_RANGE, 0, lambda: self.apply_grid(row_offset=self.row_offset.get()))

        row = tk.Frame(inner, bg=BG)
        row.pack(fill="x", pady=(dp(16), 0))
        row.grid_columnconfigure(0, weight=1, uniform="overlay")
        row.grid_columnconfigure(1, weight=1, uniform="overlay")
        self.visibility_button = Button(row, self.t("show_overlay"), self.toggle_overlay_visibility, height=38, size=9, padx=10)
        self.visibility_button.grid(row=0, column=0, sticky="ew", padx=(0, dp(4)))
        self.lock_button = Button(row, self.t("lock_overlay"), self.toggle_lock, height=38, size=9, padx=10)
        self.lock_button.grid(row=0, column=1, sticky="ew", padx=(dp(4), 0))
        self.lock_button.set_enabled(False)

    def _build_preview(self):
        inner = tk.Frame(self.preview, bg=BG)
        inner.pack(fill="both", expand=True, padx=dp(24), pady=dp(20))
        head = tk.Frame(inner, bg=BG)
        head.pack(fill="x")
        self.label(head, "preview", BG, FG, 10, True).pack(side="left")
        self.count_label = tk.Label(head, bg=BG, fg=FG, font=ui_font(10, True))
        self.count_label.pack(side="right")
        self.info_label = tk.Label(inner, bg=BG, fg=MUTED, font=ui_font(8), anchor="w", justify="left")
        self.info_label.pack(fill="x", pady=(dp(2), dp(10)))
        self.stage = tk.Canvas(inner, bg=BG, highlightthickness=0, bd=0, width=dp(240), height=dp(300))
        self.stage.pack(fill="both", expand=True)
        self.stage.bind("<Configure>", lambda _e: self._draw_stage())

        speed = tk.Frame(inner, bg=BG)
        speed.pack(fill="x", pady=(dp(14), dp(12)))
        self.label(speed, "click_speed", BG, MUTED, 9).pack(side="left")
        self.speed_value = tk.Label(speed, text=str(DEFAULT_SPEED), bg=BG, fg=FG, font=ui_font(10, True), width=2)
        self.speed_value.pack(side="right")
        self.speed = Slider(speed, SPEED_RANGE[0], SPEED_RANGE[1], DEFAULT_SPEED, lambda v: self.speed_value.configure(text=str(v)))
        self.speed.pack(side="left", fill="x", expand=True, padx=dp(14))

        actions = tk.Frame(inner, bg=BG)
        actions.pack(fill="x")
        actions.grid_columnconfigure(0, weight=1)
        self.start_button = self.button(actions, "start", self.start_placement, "primary", height=42)
        self.start_button.grid(row=0, column=0, sticky="ew")
        self.pause_button = Button(actions, self.t("pause"), self.toggle_pause, height=42, width=104)
        self.pause_button.grid(row=0, column=1, padx=(dp(8), 0))
        self.stop_button = self.button(actions, "stop", self.stop_placement, height=42, width=104)
        self.stop_button.grid(row=0, column=2, padx=(dp(8), 0))
        self.pause_button.set_enabled(False)
        self.stop_button.set_enabled(False)
        self.inputs = [self.text_area, self.limit, self.used, self.gap, self.mode_seg, self.align_seg, self.grid_x, self.grid_y, self.row_offset, self.outline_switch]

    def _arrange(self, wide):
        page = self.page
        for widget in (self.controls, self.preview, self.divider):
            widget.grid_forget()
        for index in range(3):
            page.grid_columnconfigure(index, weight=0, minsize=0)
            page.grid_rowconfigure(index, weight=0)
        if wide:
            page.grid_columnconfigure(0, minsize=dp(372))
            page.grid_columnconfigure(2, weight=1)
            page.grid_rowconfigure(0, weight=1)
            self.divider.configure(width=1, height=1)
            self.controls.grid(row=0, column=0, sticky="nsew")
            self.divider.grid(row=0, column=1, sticky="ns")
            self.preview.grid(row=0, column=2, sticky="nsew")
        else:
            page.grid_columnconfigure(0, weight=1)
            self.preview.grid(row=0, column=0, columnspan=3, sticky="nsew")
            self.divider.grid(row=1, column=0, columnspan=3, sticky="ew")
            self.controls.grid(row=2, column=0, columnspan=3, sticky="nsew")

    def _on_viewport(self, event):
        wide = event.width >= dp(880)
        if wide != self._wide:
            self._wide = wide
            self._arrange(wide)
        self.page.update_idletasks()
        total = max(event.height, self.page.winfo_reqheight())
        self.viewport.itemconfigure(self.page_window, width=event.width, height=total)
        self.viewport.configure(scrollregion=(0, 0, event.width, total))
        self._scrollable = total > event.height
        if not self._scrollable:
            self.viewport.yview_moveto(0)

    def _on_scrolled(self, first, last):
        first, last = float(first), float(last)
        if last - first >= 0.999:
            self.scroll_hint.place_forget()
            return
        height = self.viewport.winfo_height()
        self.scroll_hint.place(in_=self.viewport, relx=1.0, x=-dp(8), y=0, relheight=1.0, width=dp(5))
        self.scroll_hint.delete("all")
        self.scroll_hint.create_rectangle(0, first * height + 2, dp(5), last * height - 2, fill=LINE_STRONG, outline="")

    def _on_wheel(self, event):
        if not self._scrollable or isinstance(event.widget, tk.Text):
            return
        up = getattr(event, "num", 0) == 4 or getattr(event, "delta", 0) > 0
        self.viewport.yview_scroll(-3 if up else 3, "units")

    def _on_footer(self, event):
        reserved = self.progress_label.winfo_reqwidth() + self.credit_label.winfo_reqwidth() + dp(80)
        self.status_label.configure(wraplength=max(dp(160), event.width - reserved))

    def _reveal(self):
        self.root.update_idletasks()
        try:
            self.root.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        self.root.deiconify()
        tint_titlebar(self.root)
        self._fade(0)

    def _fade(self, step):
        try:
            self.root.attributes("-alpha", min(1.0, step / 8.0))
            if step < 8:
                self.root.after(16, self._fade, step + 1)
        except tk.TclError:
            pass

    def set_language(self, lang):
        self.lang = lang
        self.language.set(lang)
        for key, apply in self._bound:
            apply(self.t(key))
        for item in self.live_texts:
            item.refresh()
        self.mode_seg.set_labels([self.t("mode_balanced"), self.t("mode_auto"), self.t("mode_maximum")])
        self._sync_mode_help()
        self._sync_pause_button()
        self._sync_overlay_buttons()
        self._render_pattern_texts()
        self._draw_stage()
        if self.overlay is not None:
            self.overlay.refresh_texts()

    def set_mode(self, value):
        self.mode = value
        self._sync_mode_help()
        self.refresh_pattern()

    def set_align(self, value):
        self.align = value
        self.refresh_pattern()

    def set_outline(self, value):
        self.outline = bool(value)
        self.refresh_pattern()

    def _sync_mode_help(self):
        self.mode_help.configure(text=self.t(f"mode_help_{self.mode}"))

    def _sync_pause_button(self):
        self.pause_button.set_text(self.t("resume" if self.paused else "pause"))

    def _sync_overlay_buttons(self):
        overlay = self.overlay
        visible = overlay is not None and overlay.visible
        locked = visible and overlay.locked
        self.visibility_button.set_text(self.t("hide_overlay" if visible else "show_overlay"))
        self.lock_button.set_text(self.t("unlock_overlay" if locked else "lock_overlay"))
        self.lock_button.set_enabled(overlay is not None and not self.running)

    def _reset_session(self):
        self.attempted.clear()
        self.next_index = 0
        self.run_signature = None

    def _show_progress(self):
        total = self.pattern.count if self.pattern else 0
        self.progress.set("progress_idle", done=len(self.attempted), total=total)

    def _render_pattern_texts(self):
        pattern = self.pattern
        if pattern is None:
            self.count_label.configure(text="0")
            self.info_label.configure(text=self.t(self.error.key, **self.error.params) if self.error else self.t("empty_pattern"))
            return
        self.count_label.configure(text=self.t("count", count=pattern.count, available=pattern.available))
        font_label = self.t("font_detailed" if pattern.bitmap.font == FONT_DETAILED else "font_compact")
        missing = pattern.bitmap.missing
        notice = f"   {self.t('missing_chars', count=missing)}" if missing else ""
        tag = "   Outline" if pattern.bitmap.outline else ""
        self.info_label.configure(
            text=f"{font_label}   {self.t('mode_' + pattern.mode)}   Grid {pattern.resolution:.2f}x   {pattern.width} x {pattern.height}{tag}{notice}"
        )

    def _draw_stage(self):
        canvas = self.stage
        canvas.delete("all")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 40 or height < 40:
            return
        round_rect(canvas, 1, 1, width - 2, height - 2, dp(10), fill=SURFACE, outline=LINE)
        pattern = self.pattern
        if pattern is None:
            canvas.create_text(width / 2, height / 2, text=self.t("empty_pattern"), fill=FAINT, font=ui_font(10), width=width - dp(48), justify="center")
            return
        pad = dp(28)
        cell = max(1.0, min(dp(16), (width - 2 * pad) / pattern.width, (height - 2 * pad) / pattern.height))
        left = (width - pattern.width * cell) / 2
        top = (height - pattern.height * cell) / 2
        if cell >= 6 and pattern.width * pattern.height <= 4000:
            for y in range(pattern.height):
                for x in range(pattern.width):
                    if (x, y) not in pattern.points:
                        px, py = left + (x + 0.5) * cell, top + (y + 0.5) * cell
                        canvas.create_rectangle(px, py, px + 1, py + 1, fill=LINE_STRONG, outline="")
        inset = cell * 0.12 if cell >= 6 else 0
        for x, y in pattern.points:
            x0, y0 = left + x * cell, top + y * cell
            canvas.create_rectangle(x0 + inset, y0 + inset, x0 + cell - inset, y0 + cell - inset, fill=FG, outline="")

    def refresh_pattern(self):
        limit, used, gap = self.limit.get(), self.used.get(), self.gap.get()
        text = self.text_area.get()
        signature = (text, limit, used, gap, self.align, self.mode, self.outline)
        previous = self.pattern_signature
        same_inputs = (
            previous is not None and self.pattern is not None
            and previous[:3] == signature[:3] and previous[4:6] == signature[4:6]
        )
        keep = same_inputs and (previous[6] == signature[6] or self.mode == MODE_AUTO)
        res_x, res_y = (self.pattern.res_x, self.pattern.res_y) if keep else (None, None)
        try:
            pattern = fit_pattern(text, max(0, limit - used), gap, self.align, self.mode, res_x, res_y, self.outline)
            self.error = None
        except PatternError as exc:
            pattern, self.error = None, exc
        except Exception as exc:
            pattern, self.error = None, PatternError("err_calc", error=exc)
        changed = previous is not None and signature != previous
        if changed:
            self._reset_session()
        self.pattern_signature = signature
        if changed and self.repair_active:
            self.set_repair(False, "repair_off_pattern")
        self.pattern = pattern
        self._render_pattern_texts()
        self._draw_stage()
        self._show_progress()
        if pattern is not None:
            self.status.set("pattern_ready")
        else:
            self.status.set(self.error.key, **self.error.params)
        if self.overlay is not None and pattern is not None and not self.running:
            self.overlay.set_pattern(pattern)
            if self.overlay.visible:
                self.sync_grid_fields()

    def resize_pattern(self, axis, requested):
        before = self.placement_signature()
        pattern = resample_axis(self.pattern, axis, requested)
        self.pattern = pattern
        self.overlay.adopt(pattern)
        if before != self.placement_signature():
            self._reset_session()
        self._render_pattern_texts()
        self._draw_stage()
        self._show_progress()
        key = "limit_reached" if pattern.capped else "auto_active"
        self.status.set(key, x=pattern.res_x, y=pattern.res_y, count=pattern.count, available=pattern.available)

    def placement_signature(self):
        if self.pattern is None:
            return None
        pattern, overlay = self.pattern, self.overlay
        if overlay is not None:
            grid = (round(overlay.pitch_x, 2), round(overlay.pitch_y, 2), overlay.row_offset)
        else:
            grid = (self.grid_x.get(), self.grid_y.get(), self.row_offset.get())
        return (pattern.width, pattern.height, pattern.count, round(pattern.res_x, 4), round(pattern.res_y, 4), pattern.mode, pattern.bitmap.outline, *grid)

    def apply_grid(self, **values):
        if self.overlay is not None and not self.running:
            self.overlay.set_grid(**values)

    def sync_grid_fields(self):
        if self.overlay is not None:
            self.grid_x.set(round(self.overlay.pitch_x))
            self.grid_y.set(round(self.overlay.pitch_y))

    def reset_layout(self):
        if self.running:
            self.status.set("reset_blocked")
            return
        for stepper, value in ((self.grid_x, DEFAULT_PITCH), (self.grid_y, DEFAULT_PITCH), (self.row_offset, 0), (self.gap, DEFAULT_GAP)):
            stepper.set(value)
        if self.overlay is not None:
            self.overlay.set_grid(DEFAULT_PITCH, DEFAULT_PITCH, 0)
        self.pattern_signature = None
        self.refresh_pattern()
        if self.overlay is not None and self.pattern is not None and self.overlay.visible:
            self.overlay.center()
        self.status.set("layout_reset")

    def notify(self, title_key, body_key, **params):
        Dialog(self, self.t(title_key), self.t(body_key, **params), [(self.t("ok"), True, "primary")]).run()

    def confirm(self, title_key, body_key, ok="ok", cancel="cancel", **params):
        buttons = [(self.t(cancel), False, "secondary"), (self.t(ok), True, "primary")]
        return Dialog(self, self.t(title_key), self.t(body_key, **params), buttons).run()

    def show_overlay(self):
        if self.running:
            self.status.set("overlay_busy")
            return
        if self.repair_active:
            self.set_repair(False, "repair_off_overlay")
        self.refresh_pattern()
        if self.pattern is None:
            self.notify("dlg_invalid_title", self.error.key, **self.error.params)
            return
        try:
            if self.overlay is None:
                self.overlay = Overlay(self, self.pattern)
            else:
                self.overlay.show()
            self.sync_grid_fields()
        except Exception as exc:
            self.overlay = None
            self.notify("dlg_overlay_failed_title", "dlg_overlay_failed_body", error=exc)
            return
        self.overlay_state_changed()

    def hide_overlay(self):
        if self.running or self.overlay is None:
            return
        if self.repair_active:
            self.set_repair(False, "repair_off_hidden")
        self.overlay.hide()
        self.overlay_state_changed()

    def toggle_overlay_visibility(self):
        if self.running:
            self.status.set("hide_blocked")
        elif self.overlay is not None and self.overlay.visible:
            self.hide_overlay()
        else:
            self.show_overlay()

    def toggle_lock(self):
        if self.running:
            self.status.set("overlay_busy")
            return
        if self.overlay is None:
            return
        if self.repair_active:
            self.set_repair(False, "repair_off_edit")
        if not self.overlay.visible:
            self.overlay.show()
        self.overlay.set_locked(not self.overlay.locked)

    def overlay_state_changed(self):
        overlay = self.overlay
        self._sync_overlay_buttons()
        if overlay is None:
            self.status.set("ready")
        elif not overlay.visible:
            self.status.set("overlay_hidden")
        elif overlay.locked:
            self.status.set("overlay_locked")
        else:
            self.status.set("overlay_editing")

    def toggle_repair(self):
        if self.running:
            self.status.set("repair_blocked")
            return
        if self.repair_active:
            self.set_repair(False, "repair_off")
            return
        if self.mouse_listener is None:
            self.status.set("repair_no_tracker")
            return
        if self.overlay is None or not self.overlay.visible:
            self.show_overlay()
        if self.overlay is None or not self.overlay.visible:
            return
        if not self.overlay.locked:
            self.overlay.set_locked(True)
        self.set_repair(True, "repair_on")

    def set_repair(self, enabled, message_key=None):
        overlay = self.overlay
        active = bool(enabled) and overlay is not None and overlay.visible and overlay.locked
        self.repair_active = active
        self.repair_hover = None
        self.repair_since = None
        self.repair_tried = set()
        self.repair_targets = overlay.screen_points() if active else []
        if overlay is not None:
            overlay.set_hover(None)
            overlay.refresh_texts()
        if enabled and not active:
            message_key = "repair_off"
        if message_key:
            self.status.set(message_key)

    def refresh_repair_targets(self):
        self.repair_targets = self.overlay.screen_points()
        self.repair_hover = None
        self.repair_since = None
        self.repair_tried = set()
        self.overlay.set_hover(None)

    def _nearest_target(self, x, y):
        if not self.repair_targets:
            return None
        radius = max(2.0, min(12.0, min(self.overlay.pitch_x, self.overlay.pitch_y) * 0.42))
        best, best_distance = None, radius * radius
        for index, (tx, ty) in enumerate(self.repair_targets):
            distance = (tx - x) ** 2 + (ty - y) ** 2
            if distance <= best_distance:
                best, best_distance = index, distance
        return best

    def _repair_step(self):
        overlay = self.overlay
        if not (self.repair_active and not self.running and overlay is not None and overlay.visible and overlay.locked):
            return
        with self.mouse_lock:
            x, y = self.mouse_pos
        index = self._nearest_target(x, y)
        now = time.monotonic()
        if index != self.repair_hover:
            self.repair_hover = index
            self.repair_since = now if index is not None else None
            overlay.set_hover(index)
            if index is None:
                self.status.set("repair_idle")
            elif index in self.repair_tried:
                self.status.set("repair_seen", point=index + 1)
            else:
                self.status.set("repair_hover", point=index + 1)
        elif index is not None and index not in self.repair_tried and now - self.repair_since >= DWELL_SECONDS:
            self.repair_tried.add(index)
            self._click_repair(index)

    def _click_repair(self, index):
        try:
            x, y = self.repair_targets[index]
            send_click(x, y)
        except Exception as exc:
            self.repair_tried.discard(index)
            self.status.set("repair_fail", point=index + 1, error=exc)
            return
        self.attempted.add(index)
        self.status.set("repair_done", point=index + 1)
        self._show_progress()

    def start_placement(self):
        if self.repair_active:
            self.notify("dlg_repair_title", "dlg_repair_body")
            return
        if self.pattern is None:
            self.refresh_pattern()
        if self.pattern is None:
            self.notify("dlg_invalid_title", self.error.key, **self.error.params)
            return
        if self.overlay is None or not self.overlay.visible:
            self.notify("dlg_need_overlay_title", "dlg_need_overlay_body")
            return
        if not self.overlay.locked:
            self.notify("dlg_need_lock_title", "dlg_need_lock_body")
            return
        targets = self.overlay.screen_points()
        if not targets:
            self.notify("dlg_empty_title", "dlg_empty_body")
            return
        signature = self.placement_signature()
        if self.run_signature is not None and signature != self.run_signature:
            if self.next_index > 0 and not self.confirm("dlg_grid_title", "dlg_grid_body", "yes", "no"):
                return
            self._reset_session()
        self.run_signature = signature
        total = len(targets)
        if self.next_index >= total:
            if not self.confirm("dlg_done_title", "dlg_done_body", "yes", "no"):
                return
            self._reset_session()
            self.run_signature = signature
        pending = [index for index in range(self.next_index, total) if index not in self.attempted]
        if not pending:
            self.notify("dlg_nothing_title", "dlg_nothing_body")
            return
        resume = self.t("resume_from", point=pending[0] + 1) if self.next_index else self.t("from_start")
        if not self.confirm("dlg_confirm_title", "dlg_confirm_body", resume=resume, pending=len(pending), total=total, seconds=COUNTDOWN_SECONDS):
            return
        self.targets = targets
        self._begin_run(pending)

    def _set_busy(self, busy):
        for control in self.inputs:
            control.set_enabled(not busy)
        self.start_button.set_enabled(not busy)
        self.pause_button.set_enabled(busy)
        self.stop_button.set_enabled(busy)
        self.visibility_button.set_enabled(not busy)
        self.reset_button.set_enabled(not busy)
        self._sync_overlay_buttons()
        if self.overlay is not None:
            self.overlay.set_busy(busy)

    def _begin_run(self, indices):
        self.stop_event.clear()
        self.resume_event.set()
        self.running = True
        self.paused = False
        self._sync_pause_button()
        self._set_busy(True)
        self.progress.set("progress_pending", done=len(self.attempted), total=len(self.targets), pending=len(indices))
        self._countdown(COUNTDOWN_SECONDS, indices)

    def _countdown(self, seconds, indices):
        if self.stop_event.is_set():
            self._finish_run(("run_cancelled", {}))
            return
        if seconds > 0:
            self.status.set("countdown", seconds=seconds)
            self.root.after(1000, self._countdown, seconds - 1, indices)
            return
        self.status.set("placing")
        delay = max(0.055, 0.36 - self.speed.value * 0.03)
        self.worker = threading.Thread(target=self._work, args=(list(self.targets), delay, list(indices)), daemon=True)
        self.worker.start()

    def _work(self, targets, delay, indices):
        sent = 0
        last = None
        try:
            for index in indices:
                while not self.resume_event.wait(0.08):
                    if self.stop_event.is_set():
                        break
                if self.stop_event.is_set():
                    break
                x, y = targets[index]
                send_click(x, y)
                sent += 1
                last = index
                self.attempted.add(index)
                self.next_index = index + 1
                self.post(self._show_run_progress, sent, len(indices), index + 1, len(targets))
                time.sleep(delay)
            if self.stop_event.is_set():
                if last is None:
                    result = ("finish_stopped_before", {})
                else:
                    result = ("finish_stopped_after", {"point": last + 1, "sent": sent})
            else:
                self.next_index = len(targets)
                result = ("finish_done", {"sent": sent})
        except Exception as exc:
            result = ("finish_error", {"error": exc})
        self.post(self._finish_run, result)

    def _show_run_progress(self, sent, planned, point, total):
        self.progress.set("progress_run", done=len(self.attempted), total=total, sent=sent, planned=planned, point=point)

    def _finish_run(self, result):
        self.running = False
        self.paused = False
        self.resume_event.set()
        self._sync_pause_button()
        self._set_busy(False)
        self._show_progress()
        key, params = result
        self.status.set(key, **params)

    def toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused
        if self.paused:
            self.resume_event.clear()
            self.status.set("paused")
        else:
            self.resume_event.set()
            self.status.set("resumed")
        self._sync_pause_button()

    def stop_placement(self):
        if self.running:
            self.stop_event.set()
            self.resume_event.set()
            self.status.set("stopping")

    def _start_keyboard(self):
        def on_press(key):
            if key == pynput_keyboard.Key.esc:
                if self.running:
                    self.stop_event.set()
                    self.resume_event.set()
                    self.post(self.status.set, "esc_stop")
                elif self.repair_active:
                    self.post(self.set_repair, False, "esc_repair_off")
            elif key == pynput_keyboard.Key.f8:
                self.post(self.toggle_overlay_visibility)

        try:
            self.keyboard_listener = pynput_keyboard.Listener(on_press=on_press)
            self.keyboard_listener.daemon = True
            self.keyboard_listener.start()
        except Exception as exc:
            self.keyboard_listener = None
            self.status.set("warn_keyboard", error=exc)

    def _start_mouse(self):
        def on_move(x, y):
            with self.mouse_lock:
                self.mouse_pos = (int(x), int(y))

        try:
            self.mouse_listener = pynput_mouse.Listener(on_move=on_move)
            self.mouse_listener.daemon = True
            self.mouse_listener.start()
        except Exception as exc:
            self.mouse_listener = None
            self.status.set("warn_mouse", error=exc)

    def _tick(self):
        if self.closing:
            return
        while True:
            try:
                function, args = self.inbox.get_nowait()
            except queue.Empty:
                break
            try:
                function(*args)
            except tk.TclError:
                pass
        try:
            self._repair_step()
        except Exception as exc:
            self.status.set("repair_error", error=exc)
        self.root.after(TICK_MS, self._tick)

    def on_close(self):
        if self.running:
            if not self.confirm("dlg_exit_title", "dlg_exit_body", "yes", "no"):
                return
            self.stop_event.set()
            self.resume_event.set()
        self.closing = True
        for listener in (self.keyboard_listener, self.mouse_listener):
            try:
                if listener is not None:
                    listener.stop()
            except Exception:
                pass
        if self.overlay is not None:
            self.overlay.destroy()
        self.root.destroy()


def main():
    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = True
    root = tk.Tk()
    setup_metrics(root)
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
