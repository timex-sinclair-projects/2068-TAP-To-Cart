/*
 * Byte-for-byte verification that tapcart.js produces the same cartridge images
 * as the reference command-line tool (tapToCart.py).
 *
 * Reproduces the build described by tapFiles/junk.ini (subfile 3, start $8008,
 * reserved $0008, autostart, with SPECEMU.TXT and SHOTZEXR.TXT appended) and
 * compares the output to the committed tapFiles/junkBin.bin and junkDock.dck.
 *
 * Run:  node test/verify.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TapCart = require(path.join(root, 'tapcart.js'));
const tapDir = path.join(root, 'tapFiles');
const read = (f) => new Uint8Array(fs.readFileSync(path.join(tapDir, f)));

function eq(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

let failed = 0;
function check(name, cond) {
  console.log((cond ? '  ok   ' : '  FAIL ') + name);
  if (!cond) failed++;
}

// --- Parse ---
const subs = TapCart.parseTap(read('junk.TAP'));
check('parses 3 subfiles', subs.length === 3);
check('subfile names', subs.map((s) => s.name).join(',') === 'junk,junk2,junk3');
check('subfile types are Program', subs.every((s) => s.type === 0));
check('autostart detection (junk2 has run line 10)',
  subs[0].autostart === false && subs[1].autostart === true && subs[2].autostart === false);
check('subfile lengths', subs.map((s) => s.length).join(',') === '63,70,71');

// --- Build, matching tapFiles/junk.ini ---
const out = TapCart.buildCartridge({
  program: subs[2].data,
  basStart: 0x8008,
  reserved: 0x0008,
  autostart: true,
  appends: [
    { address: 0x8100, data: read('SPECEMU.TXT') },
    { address: 0x8280, data: read('SHOTZEXR.TXT') },
  ],
});

check('chunk map byte is 0xEF', out.chunkMap === 0xef);
check('.BIN matches reference (byte-for-byte)', eq(out.bin, read('junkBin.bin')));
check('.DCK matches reference (byte-for-byte)', eq(out.dck, read('junkDock.dck')));

// --- A few unit checks on padding / sizing ---
const single = TapCart.buildCartridge({ program: new Uint8Array(100) });
check('small program pads to one 8K chunk', single.bin.length === 8192);
const exact = TapCart.buildCartridge({ program: new Uint8Array(8192 - 9) }); // 8 hdr + 8183 + 1 trailer = 8192
check('exact 8K content is not over-padded', exact.bin.length === 8192);

console.log(failed ? `\n${failed} check(s) FAILED` : '\nAll checks passed.');
process.exit(failed ? 1 : 0);
