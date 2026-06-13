/*
 * tapcart.js — Timex/Sinclair 2068 TAP -> cartridge (.BIN / .DCK) conversion.
 *
 * Pure logic, no DOM. Works in the browser (attaches to window.TapCart) and in
 * Node (module.exports), so the same code that runs the web page is unit-tested
 * against the reference outputs in tapFiles/.
 *
 * Mirrors the byte layout produced by tapToCart.py. See
 * docs/Creating-TS2068-Cartridges.md for the format reference.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.TapCart = api;
})(typeof self !== 'undefined' ? self : (typeof globalThis !== 'undefined' ? globalThis : this), function () {
  'use strict';

  const CART_BASE = 0x8000; // cartridges live in the DOCK bank starting at chunk 4
  const CHUNK = 8192;       // 8K chunk / EPROM bank size
  const MAX_CART = CHUNK * 4; // chunks 4-7 = 32K usable in the DOCK

  // Spectrum/TS2068 TAP file-type codes (header byte 1).
  const TYPE_NAMES = {
    0: 'Program',
    1: 'Number array',
    2: 'Character array',
    3: 'Code',
  };

  function typeName(t) {
    return TYPE_NAMES[t] !== undefined ? TYPE_NAMES[t] : 'Unknown (' + t + ')';
  }

  function u16le(b, i) {
    return b[i] | (b[i + 1] << 8);
  }

  /*
   * Parse a TAP file (Uint8Array) into a list of subfiles.
   *
   * A TAP is a sequence of blocks, each: [2-byte little-endian length][block].
   * A 19-byte block with flag 0x00 is a header; the following block (flag 0xFF)
   * is its data. The data payload is the block minus its flag byte and trailing
   * checksum byte.
   */
  function parseTap(bytes) {
    const subfiles = [];
    const n = bytes.length;
    let pos = 0;
    let header = null;

    while (pos + 2 <= n) {
      const blockLen = u16le(bytes, pos);
      pos += 2;
      if (blockLen < 1 || pos + blockLen > n) break; // truncated / trailing junk
      const block = bytes.subarray(pos, pos + blockLen);
      pos += blockLen;

      const flag = block[0];
      if (flag === 0x00 && blockLen === 19) {
        let rawName = '';
        for (let i = 2; i < 12; i++) rawName += String.fromCharCode(block[i]);
        header = {
          type: block[1],
          name: rawName.replace(/\s+$/, ''),
          dataLength: u16le(block, 12),
          param1: u16le(block, 14),
          param2: u16le(block, 16),
        };
      } else {
        // data block: strip flag (first) and checksum (last)
        const payload = block.subarray(1, blockLen - 1);
        const data = new Uint8Array(payload); // own copy
        const h = header;
        subfiles.push({
          type: h ? h.type : null,
          name: h ? h.name : '(headerless)',
          typeLabel: h ? typeName(h.type) : 'Headerless data',
          param1: h ? h.param1 : 0,
          param2: h ? h.param2 : 0,
          length: data.length,
          // A Program autostarts if its run-line (param1) is a real line number
          // (< 0x8000). 0x8000+ means "no autostart".
          autostart: !!(h && h.type === 0 && h.param1 < 0x8000),
          data: data,
        });
        header = null;
      }
    }
    return subfiles;
  }

  /*
   * AROS chunk-specification byte. A 0 bit selects a DOCK chunk, a 1 bit selects
   * HOME. Low nibble stays 1111 (keep the OS in HOME chunks 0-3); high bits flip
   * to 0 as the cartridge grows into chunks 4..7.
   */
  function makeArosChunkMap(len) {
    if (len <= CHUNK) return 0xEF;        // chunk 4
    if (len <= CHUNK * 2) return 0xCF;    // chunks 4,5
    if (len <= CHUNK * 3) return 0x8F;    // chunks 4,5,6
    return 0x0F;                          // chunks 4,5,6,7
  }

  /*
   * Build the .BIN (ROM image) and .DCK (emulator) representations.
   *
   * opts = {
   *   program:   Uint8Array  (the BASIC program data, required)
   *   basStart:  number      (default 0x8008)
   *   autostart: boolean     (default false)
   *   reserved:  number      (HOME-bank bytes reserved for m/c vars, default 0)
   *   appends:   [{ address: number, data: Uint8Array }]  (optional CODE blocks)
   * }
   *
   * Returns { bin, dck, chunkMap, contentLength, paddedLength, chunksUsed }.
   */
  function buildCartridge(opts) {
    if (!opts || !opts.program) throw new Error('A BASIC program is required.');
    const basStart = opts.basStart != null ? opts.basStart : 0x8008;
    const reserved = opts.reserved != null ? opts.reserved : 0;
    const autostart = !!opts.autostart;
    const program = opts.program;
    const appends = (opts.appends || []).slice().sort((a, b) => a.address - b.address);

    // 8-byte ROS header (chunk-map byte filled in after the size is known).
    const rom = [];
    rom.push(1);                 // 0: language = BASIC (+ machine code)
    rom.push(2);                 // 1: cartridge type = AROS
    rom.push(basStart & 0xff);   // 2: start address low
    rom.push((basStart >> 8) & 0xff); // 3: start address high
    rom.push(0);                 // 4: chunk spec (placeholder)
    rom.push(autostart ? 1 : 0); // 5: autostart
    rom.push(reserved & 0xff);   // 6: reserved low
    rom.push((reserved >> 8) & 0xff); // 7: reserved high

    // BASIC program + end marker (must be >= 128; tapToCart uses 0x80).
    for (let i = 0; i < program.length; i++) rom.push(program[i]);
    rom.push(0x80);

    const programRegionEnd = rom.length; // end of the BASIC region

    // Append CODE blocks at their target addresses, zero-filling any gaps.
    for (const ap of appends) {
      const offset = ap.address - CART_BASE;
      if (offset < programRegionEnd) {
        throw new Error('Append at $' + hex(ap.address) + ' overlaps the BASIC program.');
      }
      if (offset < rom.length) {
        throw new Error('Append at $' + hex(ap.address) + ' overlaps a previous file.');
      }
      while (rom.length < offset) rom.push(0x00);
      for (let i = 0; i < ap.data.length; i++) rom.push(ap.data[i]);
    }

    const contentLength = rom.length;
    const chunkMap = makeArosChunkMap(contentLength);
    rom[4] = chunkMap;

    // Pad up to a whole number of 8K chunks (no extra chunk when already aligned).
    const pad = (CHUNK - (rom.length % CHUNK)) % CHUNK;
    for (let i = 0; i < pad; i++) rom.push(0x00);

    const bin = new Uint8Array(rom);

    // .DCK = 9-byte header (bank id + per-chunk type) followed by the ROM image.
    // Per chunk: 0 = absent, 2 = ROM. Chunks the AROS map marks as DOCK become ROM.
    const dck = new Uint8Array(9 + bin.length);
    if ((chunkMap & 0x10) === 0) dck[5] = 2; // chunk 4
    if ((chunkMap & 0x20) === 0) dck[6] = 2; // chunk 5
    if ((chunkMap & 0x40) === 0) dck[7] = 2; // chunk 6
    if ((chunkMap & 0x80) === 0) dck[8] = 2; // chunk 7
    dck.set(bin, 9);

    return {
      bin: bin,
      dck: dck,
      chunkMap: chunkMap,
      contentLength: contentLength,
      paddedLength: bin.length,
      chunksUsed: bin.length / CHUNK,
    };
  }

  function hex(n) {
    return n.toString(16).toUpperCase();
  }

  return {
    CART_BASE: CART_BASE,
    CHUNK: CHUNK,
    MAX_CART: MAX_CART,
    typeName: typeName,
    parseTap: parseTap,
    makeArosChunkMap: makeArosChunkMap,
    buildCartridge: buildCartridge,
  };
});
