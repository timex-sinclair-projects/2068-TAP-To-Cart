# 2068 TAP → Cartridge

Convert a Timex/Sinclair 2068 `.TAP` (tape) file containing a BASIC program into a
cartridge image:

- **`.BIN`** — a ROM image in AROS (Application ROM Oriented Software) format, ready
  to burn to an EPROM.
- **`.DCK`** — a DOCK cartridge file used by TS2068 emulators.

Output is always padded to a multiple of 8192 bytes (8K cartridge banks). You can
optionally append extra binary/machine-code files after the BASIC program.

There are two ways to use it: a **web app** (no install) and a **command-line tool**.

---

## 🌐 Web app (no install)

Open the builder in your browser — it runs entirely client-side, so nothing is
uploaded anywhere:

**→ https://timex-sinclair-projects.github.io/2068-TAP-To-Cart/**

Drag in a `.TAP`, pick the BASIC program (and optionally append CODE blocks at their
load addresses), set any header options, then download the `.BIN` and `.DCK`.

You can also just open [`index.html`](index.html) locally with a double-click.

---

## 💻 Command-line tool

Requires Python 3.

```sh
# Quick: convert the first program in a TAP with defaults
python3 tapToCart.py tapFiles/junk.TAP

# Full control via an .ini control file (subfile choice, addresses,
# appended binaries, output names, autostart, …)
python3 tapToCart.py mycart.ini
```

A control file is a plain INI file; see [`junk.ini`](junk.ini) and
[`tapFiles/junk.ini`](tapFiles/junk.ini) for fully-commented examples, and the
guide below for every field.

---

## 📖 Documentation

- **[A Beginner's Guide to Creating TS2068 Cartridges](docs/Creating-TS2068-Cartridges.md)**
  — what a cartridge is, the bank/chunk memory model, the 8-byte ROS header, the
  `.BIN`/`.DCK` formats, DOCK BASIC limitations, and how this tool maps onto all of
  it. Start here if the format is new to you.

The guide synthesizes period manuals by Thomas B. Woods and Bob Orrfelt, hosted on
the Internet Archive (linked from the guide).

---

## 🗂 Repository layout

| Path | What it is |
|------|------------|
| [`index.html`](index.html), [`tapcart.js`](tapcart.js) | The browser app (UI + pure conversion logic) |
| [`tapToCart.py`](tapToCart.py), [`utils/`](utils) | The command-line tool |
| [`docs/`](docs) | Format guide + a transcription of the NVM RAM manual |
| [`tapFiles/`](tapFiles) | Sample `junk.TAP` and reference `.bin`/`.dck` outputs |
| [`test/verify.mjs`](test/verify.mjs) | Verifies the web app's output matches the CLI byte-for-byte |

The web and CLI paths produce the same cartridge format; `test/verify.mjs` checks
the JavaScript output against the reference files in `tapFiles/` byte-for-byte:

```sh
node test/verify.mjs
```

---

## License

See [LICENSE](LICENSE).
