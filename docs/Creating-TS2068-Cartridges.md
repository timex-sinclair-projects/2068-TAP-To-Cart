# A Beginner's Guide to Creating TS2068 Cartridges

This guide explains what a Timex/Sinclair 2068 cartridge actually *is*, how the
machine decides what to do with one, and how this project (`tapToCart.py`) turns
an ordinary BASIC tape file into a cartridge image you can run in an emulator or
burn to an EPROM.

It is written for someone who has never made a cartridge before. If you only want
to *use* the tool, jump to [Using this tool](#using-this-tool). If you want to
understand *why* it produces the bytes it does, read from the top.

> **In a hurry?** There's a browser-based builder that does all of this with no
> install — drag in a `.TAP`, pick what to include, and download the `.BIN`/`.DCK`:
> **<https://timex-sinclair-projects.github.io/2068-TAP-To-Cart/>**
> (source: [`index.html`](../index.html)). The rest of this guide explains what it
> produces and why.

> **Sources.** This guide synthesizes two period manuals, both scanned and freely
> readable on the Internet Archive:
> - Thomas B. Woods, *The 32K Non-Volatile RAM Owner's Manual* (1985–86) — the
>   cartridge concepts. [archive.org](https://archive.org/details/thomas-woods/The%2032K%20Non-Volatile%20RAM%20Owner%27s%20Manual/mode/2up)
>   · companion: *32/64K Non-Volatile RAM Board for the T/S 2068*
>   [archive.org](https://archive.org/details/thomas-woods/32K%2064K%20Non%20Volatile%20RAM%20Board%20for%20the%20TS%202068%20Computer/mode/2up)
> - Bob Orrfelt, *Dock It — EPROM Programmer Manual for the TS2068* (1985) — the
>   EPROM/cartridge mechanics and the system configuration table.
>   [archive.org](https://archive.org/details/bob-orrfelt/Dock%20It%20-%20EPROM%20Programmer%20Manual%20for%20the%20TS2068%20Computer/page/n27/mode/2up)
>
> Both are excellent primary references and agree with each other; where this guide
> states a specific byte value, it comes from those manuals and matches what the
> code in this repository writes. A text transcription of the NVM RAM board manual
> is kept in [`docs/`](.) for quick searching.

---

## 1. The big picture: banks and chunks

The Z80 in the TS2068 can only "see" 64K of memory at once. Timex worked around
this with **banked memory**: the machine can switch between three separate 64K
banks, but only ever exposes 64K to the Z80 at a time.

The three banks are:

| Bank   | Number | What lives there normally                                   |
|--------|--------|-------------------------------------------------------------|
| HOME   | 255    | The BASIC ROM, your program, variables, the screen — normal operation |
| DOCK   | 0      | **The cartridge port** (the door on the front of the machine) |
| EXROM  | 254    | The 8K "extra" ROM used for SAVE/LOAD/VERIFY/MERGE          |

Each 64K bank is divided into eight **8K chunks**, numbered 0–7:

| Chunk | Address range      |
|-------|--------------------|
| 0     | `$0000`–`$1FFF`    |
| 1     | `$2000`–`$3FFF`    |
| 2     | `$4000`–`$5FFF`    |
| 3     | `$6000`–`$7FFF`    |
| 4     | `$8000`–`$9FFF`    |
| 5     | `$A000`–`$BFFF`    |
| 6     | `$C000`–`$DFFF`    |
| 7     | `$E000`–`$FFFF`    |

The clever part: the machine can **mix chunks from two banks**. You can ask for,
say, chunks 4–7 from the DOCK bank and chunks 0–3 from the HOME bank at the same
time. (Hardware-wise this is done by writing to I/O port 244; the cartridge ROS
header, below, does it for you automatically.)

**Why chunk 4 matters.** Cartridges live in the DOCK bank starting at chunk 4
(`$8000` = 32768 decimal). Chunks 0–3 of the HOME bank hold the BASIC operating
system and must stay switched in — turning them off crashes the machine. So a
cartridge program is loaded into chunks 4–7 of the DOCK, leaving the OS untouched
in HOME chunks 0–3.

This is why everything in this tool revolves around `$8000` and multiples of 8192.

---

## 2. How the 2068 recognizes a cartridge: the 8-byte ROS header

When you power on (or after `NEW`), the TS2068's startup routine switches in the
DOCK bank and reads the **first 8 bytes at `$8000`** (32768). These bytes are the
**ROS header** (ROS = "Rom Oriented Software", sometimes called the "ROS overhead
bytes"). They tell the machine what kind of cartridge this is and how to run it.

| Byte | Address       | Meaning            | Values                                                                 |
|------|---------------|--------------------|------------------------------------------------------------------------|
| 0    | `$8000`/32768 | Language type      | `1` = BASIC (may also contain machine code) · `2` = machine code only  |
| 1    | `$8001`/32769 | Cartridge type     | `1` = LROS · `2` = AROS                                                 |
| 2–3  | `$8002`/32770 | Start of program   | 2-byte address, little-endian (low byte first)                         |
| 4    | `$8004`/32772 | Chunk specification | bitmap — see below                                                     |
| 5    | `$8005`/32773 | Autostart          | `0` = no · `1` = yes                                                    |
| 6–7  | `$8006`/32774 | Reserved bytes     | bytes reserved in the HOME bank for machine-code variables (usually 0) |

### LROS vs AROS

- **LROS** (*Language* ROS) **replaces** the operating system. On boot the machine
  reads byte 1, switches in the chunks named by byte 4, and *jumps* to the address
  in bytes 2–3. From then on the cartridge is in charge. The Spectrum emulator
  cartridge is a classic LROS.

- **AROS** (*Application* ROS) runs *alongside* BASIC. There are two flavors:
  - **BASIC AROS** — a BASIC program stored in the DOCK. The machine pulls one
    program line at a time out of the cartridge into a small buffer (the "AROS
    buffer") in HOME chunk 3, switches HOME back in, and executes that line. Your
    variables live in the HOME bank, so you get more room for data and near-instant
    "loading."
  - **Machine-code AROS** — machine code that gets copied out of the cartridge into
    a working RAM configuration and run.

**This tool produces BASIC AROS cartridges** (`language type = 1`, `cartridge type
= 2`). That is the common case: take a BASIC program off tape and make it a
cartridge.

### The chunk specification byte (byte 4)

Byte 4 is a bitmap with one bit per chunk. The convention for an **AROS** is:

- bit = `0` → that chunk is taken from the **DOCK** (the cartridge)
- bit = `1` → that chunk is taken from the **HOME** bank

Bits are numbered 0–7 for chunks 0–7. Since a cartridge occupies chunks 4 and up,
only the high bits change. The values this tool emits:

| Program + appended data size | Chunks used in DOCK | Byte 4 value | Binary       |
|------------------------------|---------------------|--------------|--------------|
| ≤ 8K                         | 4                   | `$EF`        | `1110 1111`  |
| ≤ 16K                        | 4, 5                | `$CF`        | `1100 1111`  |
| ≤ 24K                        | 4, 5, 6             | `$8F`        | `1000 1111`  |
| ≤ 32K                        | 4, 5, 6, 7          | `$0F`        | `0000 1111`  |

Read `$EF` = `1110 1111`: the low four bits (`1111`) keep HOME chunks 0–3 (the OS);
bit 4 is `0`, so chunk 4 comes from the DOCK; bits 5–7 are `1`, so chunks 5–7 stay
HOME. That's a single 8K cartridge. As the program grows, more high bits flip to
`0` to pull in more DOCK chunks. (In the code this is
[`makeArosChunkMap()`](../utils/tapDckRtns.py).)

### A worked example (straight from the manuals)

A typical small BASIC AROS, written as `POKE`s, looks like this:

```
POKE 32768,1     : REM language = BASIC
POKE 32769,2     : REM type = AROS
POKE 32770,8     : REM start address low byte  ($8008 = 32776)
POKE 32771,128   : REM start address high byte
POKE 32772,15    : REM chunk spec ($0F = chunks 4-7 in DOCK)
POKE 32773,1     : REM autostart = yes
POKE 32774,0     : REM reserved low
POKE 32775,0     : REM reserved high
```

The program itself begins at `$8008` (32776) — the eighth byte after the start of
chunk 4, immediately following the 8-byte header.

---

## 3. The two output files

This tool writes **two** representations of the same cartridge.

### The `.bin` (ROM) file

A raw ROM image: the 8-byte ROS header, followed by the BASIC program data, an end
marker, optional appended binary files, and zero-padding. This is what you'd burn
onto an EPROM (a 2764 8K or 27128 16K chip, per the *Dock It* manual).

Two details the manuals call out, both handled for you:

- **The end marker.** The byte immediately after the BASIC program must be ≥ 128.
  This tool writes `$80` (128). Leaving it at this value satisfies the requirement
  and signals end-of-program to the AROS interpreter.
- **8K alignment.** Cartridge ROM is organized in 8K chunks, so the image is padded
  with `$00` up to the next multiple of 8192 bytes
  ([`padRomFile()`](../tapToCart.py)).

### The `.dck` (DOCK) file

The `.dck` format is what TS2068 **emulators** load. It is the ROM image prefixed
with a small header that describes, chunk by chunk, what kind of memory each 8K
chunk is.

The DCK header this tool writes is 9 bytes:

- **Byte 0** — the bank ID. `0` = DOCK bank.
- **Bytes 1–8** — one status byte per chunk (chunks 0–7):
  - `0` = chunk not present in this cartridge
  - `2` = ROM (present)

The tool derives these from the chunk-spec byte: every chunk the ROS header marks
as living in the DOCK is flagged `2` (ROM) in the DCK header, the rest stay `0`
([`makeDockHdr()`](../utils/tapDckRtns.py)). So an 8K cartridge (`$EF`) marks only
chunk 4 as ROM; a 32K cartridge (`$0F`) marks chunks 4–7.

After the header, the full ROM image is copied verbatim.

---

## 4. Using this tool

### Requirements

Python 3. Run from the project root.

### Mode A — quick conversion of a single TAP

If you just have a `.tap` file with one BASIC program and want defaults:

```
python3 tapToCart.py tapFiles/junk.TAP
```

This converts the **first** subfile in the TAP using fixed defaults
(start address `$8008`, no autostart override, no appended files) and writes
`junk.bin` and `junk.dck` next to the TAP.

### Mode B — full control via an `.ini` control file

For multi-subfile TAPs, custom start addresses, autostart, custom output names, or
appended binary files, pass a control file instead:

```
python3 tapToCart.py mycart.ini
```

A control file is a plain INI file. Here is an annotated minimal example (see
[`junk.ini`](../junk.ini) and [`tapFiles/junk.ini`](../tapFiles/junk.ini) for the
fully-commented originals):

```ini
[TOP]
; Magic value that marks this as a valid control file. Copy it verbatim.
Sentinel = 5>Ychs+IhFd[U:q`[tDg`x>[=u=vYFFG

[TAPFILE]
; Which subfile inside a multi-program TAP to convert (1-based).
; Omit if there is only one program in the TAP.
subfile = 3
; The TAP file to read. Quotes optional. Relative paths allowed.
; Avoid spaces in file names.
tapfile = "tapFiles/junk.TAP"

[HDRDAT]
; ROM start address of the BASIC program. Default $8008 if omitted.
basStart = $8008
; Space reserved in the HOME bank for machine-code variables. Default 0.
varSpace = $0008
; Force autostart. Ignored if the BASIC program already autostarts
; (i.e. it was saved with a LINE number). Honored otherwise.
autoStart = 1

[OUTFILES]
; Output names. If omitted, the TAP name is reused with .bin / .dck.
binFile = "tapFiles/junkBin.bin"
dckFile = "tapFiles/junkDock.dck"

[BINFILES]
; Optional. Extra files appended after the BASIC program, each at a
; given TS2068 address. List them in ascending address order; gaps are
; zero-filled. The key name (binFile1, binFile3...) can be anything
; unique. Format:  address, "path"
binFile1 = $8100, "tapFiles/SPECEMU.TXT"
binFile3 = $8280, "tapFiles/SHOTZEXR.TXT"
```

Notes:

- **Numbers** may be decimal or hex with a leading `$` (e.g. `$8008`).
- **The `[TOP]` sentinel is mandatory** — it's a sanity check so the tool doesn't
  try to process a random INI. Copy it exactly.
- **Autostart** from the control file is only a fallback. If the BASIC program in
  the TAP was saved to autorun (its start parameter is below `$8000`), that wins.
- **Appended files** must not overlap the BASIC program or each other; the tool
  aborts if a file's address would overwrite memory already used, and zero-fills
  any gap between files.

---

## 5. Limitations of DOCK BASIC programs

Because a BASIC AROS runs one line at a time out of the cartridge (not the normal
HOME execution path), some BASIC features don't work. From the *Dock It* manual:

- **Variables must be initialized by a program line** (e.g. `LET A$="Hi"`), because
  the cartridge has no saved variables of its own — only the program text.
- **No `DEF FN` / `FN`.** Replace user-defined functions with their expressions.
- **No 64-column (dual) video mode.**
- **No calculated `GO TO` / `GO SUB`** (e.g. `GO TO (1000+n*10)` won't work).
- **`FOR…NEXT` loops cannot change their limit mid-loop.**
- **`USR` calls only work at certain addresses.** There is a known bug in the DOCK
  `USR` routine; only specific address ranges within each chunk are valid (the
  *Dock It* manual prints the full table). Also, machine code called via `USR`
  should not straddle a chunk boundary — only the chunk containing the call address
  is switched in.
- `PEEK`, `POKE`, and all tape/disk commands act on the **HOME** bank only.

If your BASIC program respects these rules, it will run from the cartridge with no
changes.

---

## 6. From `.bin` to a real cartridge (EPROM)

The `.dck` file is all you need for emulators. To make *physical* hardware, the
`.bin` image is burned onto an EPROM and plugged into the DOCK:

- **8K** programs fit a **2764** EPROM; up to **16K** fits a **27128**.
- Period hardware like the GESSO EPROM Programmer (*Dock It*) or a battery-backed
  NVM RAM board (Woods) could host the image. The NVM board is especially handy
  during development: you can write and rewrite the cartridge image in
  battery-backed RAM without burning a new chip each time, then commit to EPROM
  once the program is debugged.

These hardware paths are beyond what this tool does — it stops at producing correct
`.bin` and `.dck` images — but the manuals linked at the top of this guide cover
them in full if you want to build the real thing.

---

## Quick reference

```
ROS header @ $8000 (8 bytes):
  +0  language   1=BASIC(+mc)  2=machine code only
  +1  type       1=LROS        2=AROS
  +2  start addr (lo)          \ little-endian, e.g. $8008
  +3  start addr (hi)          /
  +4  chunk spec  0-bit=DOCK, 1-bit=HOME  ($EF/$CF/$8F/$0F for 8/16/24/32K)
  +5  autostart  0=no 1=yes
  +6  reserved (lo)
  +7  reserved (hi)
Program data starts at $8008. End marker byte = $80. Pad to 8K boundary.

DCK header (9 bytes): [bank=0][chunk0..chunk7]  per chunk: 0=absent, 2=ROM
```
