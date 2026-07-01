/**
 * Generate placeholder icons for electron-builder.
 * Run: node scripts/generate-icons.mjs
 *
 * Creates assets/icon.png (256x256).
 * electron-builder auto-converts PNG to .ico/.icns as needed.
 * Replace with a proper icon for production.
 */

import { writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { deflateSync } from "zlib";

const __dirname = dirname(fileURLToPath(import.meta.url));
const assetsDir = join(__dirname, "..", "assets");

mkdirSync(assetsDir, { recursive: true });

const width = 512;
const height = 512;

// Create RGBA pixel data
const pixels = Buffer.alloc(width * height * 4);

for (let y = 0; y < height; y++) {
  for (let x = 0; x < width; x++) {
    const offset = (y * width + x) * 4;

    // Background: #6366f1 (indigo)
    let r = 0x63;
    let g = 0x66;
    let b = 0xf1;
    let a = 255;

    // Rounded rectangle with 80px corner radius
    const margin = 32;
    const cr = 80;
    const lx = x - margin;
    const ly = y - margin;
    const rx = width - margin - 1 - x;
    const ry = height - margin - 1 - y;
    const inside = lx >= 0 && ly >= 0 && rx >= 0 && ry >= 0;

    if (!inside) {
      r = 0; g = 0; b = 0; a = 0;
    } else {
      // Corner cutouts
      const inTopLeft = lx < cr && ly < cr;
      const inTopRight = rx < cr && ly < cr;
      const inBottomLeft = lx < cr && ry < cr;
      const inBottomRight = rx < cr && ry < cr;

      if (inTopLeft && Math.hypot(lx - cr, ly - cr) > cr) {
        r = 0; g = 0; b = 0; a = 0;
      } else if (inTopRight && Math.hypot(rx - cr, ly - cr) > cr) {
        r = 0; g = 0; b = 0; a = 0;
      } else if (inBottomLeft && Math.hypot(lx - cr, ry - cr) > cr) {
        r = 0; g = 0; b = 0; a = 0;
      } else if (inBottomRight && Math.hypot(rx - cr, ry - cr) > cr) {
        r = 0; g = 0; b = 0; a = 0;
      } else {
        // Draw "M" letter in white
        const cx = width / 2;
        const cy = height / 2;
        const lw = 180;
        const lh = 180;
        const left = cx - lw / 2;
        const top = cy - lh / 2;
        const t = 24; // stroke thickness

        const inLeft = x >= left && x < left + t && y >= top && y < top + lh;
        const inRight = x >= left + lw - t && x < left + lw && y >= top && y < top + lh;

        // Diagonals: approximate with simple checks
        const nx = (x - left) / lw; // 0..1
        const ny = (y - top) / lh;  // 0..1
        const inLeftDiag = ny < 0.5 && Math.abs(ny - nx) < 0.08 && x >= left && x < cx;
        const inRightDiag = ny < 0.5 && Math.abs(ny - (1 - nx)) < 0.08 && x >= cx && x < left + lw;

        if (inLeft || inRight || inLeftDiag || inRightDiag) {
          r = 255; g = 255; b = 255;
        }
      }
    }

    pixels[offset] = r;
    pixels[offset + 1] = g;
    pixels[offset + 2] = b;
    pixels[offset + 3] = a;
  }
}

// Encode as PNG
const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

const ihdrData = Buffer.alloc(13);
ihdrData.writeUInt32BE(width, 0);
ihdrData.writeUInt32BE(height, 4);
ihdrData[8] = 8;
ihdrData[9] = 6; // RGBA
const ihdr = pngChunk("IHDR", ihdrData);

const rawRows = Buffer.alloc(height * (1 + width * 4));
for (let y = 0; y < height; y++) {
  rawRows[y * (1 + width * 4)] = 0; // filter: none
  pixels.copy(rawRows, y * (1 + width * 4) + 1, y * width * 4, (y + 1) * width * 4);
}
const idat = pngChunk("IDAT", deflateSync(rawRows));
const iend = pngChunk("IEND", Buffer.alloc(0));

const png = Buffer.concat([signature, ihdr, idat, iend]);

writeFileSync(join(assetsDir, "icon.png"), png);
console.log("Created assets/icon.png (512x512 placeholder)");
console.log("electron-builder will auto-convert to .ico/.icns as needed.");
console.log("Replace with a proper icon for production builds.");

function pngChunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const typeBuf = Buffer.from(type, "ascii");
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([len, typeBuf, data, crc]);
}

function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    c ^= buf[i];
    for (let j = 0; j < 8; j++) {
      c = c & 1 ? (c >>> 1) ^ 0xedb88320 : c >>> 1;
    }
  }
  return (c ^ 0xffffffff) >>> 0;
}
