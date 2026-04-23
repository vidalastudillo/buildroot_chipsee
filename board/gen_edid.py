#!/usr/bin/env python3
"""
Generate a synthetic 128-byte EDID 1.3 binary for Raspberry Pi displays
that have no DDC EEPROM (e.g. HDMI-to-DPI bridge panels).

Usage
-----
  python3 board/gen_edid.py [PROFILE]

  PROFILE defaults to "cs10600ra4070" if omitted.
  Run with --list to see available profiles.

Output
------
  rootfs_overlay/lib/firmware/edid_<profile>.bin

Reference in cmdline.txt
------------------------
  drm.edid_firmware=HDMI-A-1:edid_<profile>.bin

Adding a new display profile
-----------------------------
  Copy an existing entry in PROFILES below and adjust the values.
  All timing parameters map directly to the RPi hdmi_timings format:
    hdmi_timings=<h_active> <h_sync_pol> <h_fp> <h_sync> <h_bp>
                 <v_active> <v_sync_pol> <v_fp> <v_sync> <v_bp>
                 ... <pixel_clock_hz> ...

  h_sync_pol / v_sync_pol: 0 = negative, 1 = positive
"""

import struct
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Display profiles
# Each entry maps to one hdmi_timings line from the manufacturer's config.txt.
# ---------------------------------------------------------------------------
PROFILES = {
    # Chipsee PPC-CM4-070  (CS10600RA4070P)  — 7-inch 1024×600
    # hdmi_timings=1024 0 160 10 160 600 0 12 1 23 0 0 0 60 0 52000000 6
    "cs10600ra4070": dict(
        h_active=1024, h_front_porch=160, h_sync_pulse=10, h_back_porch=160,
        h_sync_pol=0,
        v_active=600,  v_front_porch=12,  v_sync_pulse=1,  v_back_porch=23,
        v_sync_pol=0,
        pixel_clock_hz=52_000_000,
        mfr="CSY", product=0x4070,
        name="CS10600RA4070",
        h_mm=154, v_mm=86,
    ),

    # Chipsee PPC-CM4-101  (CS12800RA4101)  — 10.1-inch 1280×800
    # hdmi_timings=1280 1 72 20 68 800 1 15 2 21 0 0 0 60 0 72400000 5
    "cs12800ra4101": dict(
        h_active=1280, h_front_porch=72,  h_sync_pulse=20, h_back_porch=68,
        h_sync_pol=1,
        v_active=800,  v_front_porch=15,  v_sync_pulse=2,  v_back_porch=21,
        v_sync_pol=1,
        pixel_clock_hz=72_400_000,
        mfr="CSY", product=0x4101,
        name="CS12800RA4101",
        h_mm=216, v_mm=135,
    ),
}

# ---------------------------------------------------------------------------
# EDID builder
# ---------------------------------------------------------------------------

def make_mfr_id(s: str) -> bytes:
    """Encode 3-letter EDID manufacturer ID (big-endian packed 5-bit chars)."""
    assert len(s) == 3 and s.isalpha(), f"Invalid manufacturer ID: {s!r}"
    b = [ord(c.upper()) - ord('A') + 1 for c in s]
    return struct.pack('>H', (b[0] << 10) | (b[1] << 5) | b[2])


def monitor_name_descriptor(name: str) -> bytes:
    d = bytearray(18)
    d[0:5] = b'\x00\x00\x00\xFC\x00'
    payload = (name[:12] + '\n').encode('ascii')
    d[5:5 + len(payload)] = payload
    for i in range(5 + len(payload), 18):
        d[i] = 0x20
    return bytes(d)


def null_descriptor() -> bytes:
    d = bytearray(18)
    d[3] = 0x10
    return bytes(d)


def build_cea_extension() -> bytes:
    cea = bytearray(128)
    cea[0] = 0x02  # CEA-861 extension tag
    cea[1] = 0x03  # CEA-861 revision 3
    cea[2] = 0x0A  # DTD offset = 10 (4-byte header + 6-byte VSDB, no DTDs)
    cea[3] = 0x00  # no underscan, no audio, no YCbCr 4:4:4, no YCbCr 4:2:2
    # HDMI VSDB (6 bytes): IEEE OUI 0x000C03 = HDMI Licensing LLC
    # Presence of VSDB makes drm_detect_hdmi_monitor() return true, causing
    # the vc4 driver to send AVI infoframes with colorspace=RGB.
    cea[4] = 0x65  # vendor specific tag (3<<5)|5, length=5
    cea[5] = 0x03  # OUI byte 0
    cea[6] = 0x0C  # OUI byte 1
    cea[7] = 0x00  # OUI byte 2
    cea[8] = 0x10  # physical address high: 1.0.x.x
    cea[9] = 0x00  # physical address low:  x.x.0.0
    # bytes 10–126: zeros (no DTDs, no additional data blocks)
    cea[127] = (-sum(cea[:127])) & 0xFF
    return bytes(cea)


def build_edid(p: dict) -> bytes:
    h_blank = p['h_front_porch'] + p['h_sync_pulse'] + p['h_back_porch']
    v_blank = p['v_front_porch'] + p['v_sync_pulse'] + p['v_back_porch']
    clk_10k = p['pixel_clock_hz'] // 10_000

    edid = bytearray(128)

    # Fixed header
    edid[0:8] = b'\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00'

    edid[8:10]  = make_mfr_id(p['mfr'])
    edid[10:12] = struct.pack('<H', p['product'])
    edid[12:16] = b'\x00\x00\x00\x00'          # serial: unused
    edid[16]    = 1                              # week 1
    edid[17]    = 35                             # year 1990+35 = 2025
    edid[18]    = 1                              # EDID version
    edid[19]    = 3                              # EDID revision
    edid[20]    = 0x80                           # digital input
    edid[21]    = max(1, p['h_mm'] // 10)        # cm (rounded)
    edid[22]    = max(1, p['v_mm'] // 10)
    edid[23]    = 0x78                           # gamma 2.2
    edid[24]    = 0x06                           # preferred timing in DTD1 + sRGB color space
    edid[25:35] = b'\xEE\x91\xA3\x54\x4C\x99\x26\x0F\x50\x54'  # sRGB primaries + D65 white
    edid[35:38] = b'\x00\x00\x00'               # established timings: none
    for i in range(8):                           # standard timings: unused
        edid[38 + i * 2]     = 0x01
        edid[38 + i * 2 + 1] = 0x01

    # Detailed Timing Descriptor 1 (bytes 54–71)
    o = 54
    struct.pack_into('<H', edid, o, clk_10k)
    edid[o+2]  = p['h_active'] & 0xFF
    edid[o+3]  = h_blank & 0xFF
    edid[o+4]  = ((p['h_active'] >> 8) & 0x0F) << 4 | ((h_blank >> 8) & 0x0F)
    edid[o+5]  = p['v_active'] & 0xFF
    edid[o+6]  = v_blank & 0xFF
    edid[o+7]  = ((p['v_active'] >> 8) & 0x0F) << 4 | ((v_blank >> 8) & 0x0F)
    edid[o+8]  = p['h_front_porch'] & 0xFF
    edid[o+9]  = p['h_sync_pulse']  & 0xFF
    edid[o+10] = ((p['v_front_porch'] & 0x0F) << 4) | (p['v_sync_pulse'] & 0x0F)
    edid[o+11] = (((p['h_front_porch'] >> 8) & 0x03) << 6) | \
                 (((p['h_sync_pulse']  >> 8) & 0x03) << 4) | \
                 (((p['v_front_porch'] >> 4) & 0x03) << 2) | \
                  ((p['v_sync_pulse']  >> 4) & 0x03)
    edid[o+12] = p['h_mm'] & 0xFF
    edid[o+13] = p['v_mm'] & 0xFF
    edid[o+14] = ((p['h_mm'] >> 8) & 0x0F) << 4 | ((p['v_mm'] >> 8) & 0x0F)
    edid[o+15] = 0x00                            # h border
    edid[o+16] = 0x00                            # v border
    # flags: non-interlaced | digital separate sync | h/v polarity
    edid[o+17] = 0x18 | (p['h_sync_pol'] << 2) | (p['v_sync_pol'] << 1)

    edid[72:90]   = monitor_name_descriptor(p['name'])
    edid[90:108]  = null_descriptor()
    edid[108:126] = null_descriptor()
    edid[126]     = 0x01                         # one CEA-861 extension follows
    edid[127]     = (-sum(edid[:127])) & 0xFF    # checksum

    return bytes(edid) + build_cea_extension()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if '--list' in args:
        print("Available profiles:")
        for name, p in PROFILES.items():
            fps = int(p['pixel_clock_hz']) / (
                (int(p['h_active']) + int(p['h_front_porch']) + int(p['h_sync_pulse']) + int(p['h_back_porch'])) *
                (int(p['v_active']) + int(p['v_front_porch']) + int(p['v_sync_pulse']) + int(p['v_back_porch']))
            )
            print(f"  {name:20s}  {p['h_active']}x{p['v_active']}@{fps:.0f}Hz  —  {p['name']}")
        sys.exit(0)

    profile_name = args[0] if args else 'cs10600ra4070'

    if profile_name not in PROFILES:
        print(f"Unknown profile '{profile_name}'. Use --list to see options.", file=sys.stderr)
        sys.exit(1)

    p = PROFILES[profile_name]
    edid = build_edid(p)

    out = Path('rootfs_overlay/lib/firmware') / f'edid_{profile_name}.bin'
    out.write_bytes(edid)

    h_total = int(p['h_active']) + int(p['h_front_porch']) + int(p['h_sync_pulse']) + int(p['h_back_porch'])
    v_total = int(p['v_active']) + int(p['v_front_porch']) + int(p['v_sync_pulse']) + int(p['v_back_porch'])
    fps = int(p['pixel_clock_hz']) / (h_total * v_total)

    print(f"Written : {out}  ({len(edid)} bytes)")
    print(f"Profile : {profile_name}  ({p['name']})")
    print(f"Clock   : {int(p['pixel_clock_hz']) / 1e6:.2f} MHz")
    print(f"Geometry: {p['h_active']}x{p['v_active']}  HTotal={h_total}  VTotal={v_total}")
    print(f"FPS     : {fps:.2f} Hz")
    print(f"Checksum: 0x{edid[127]:02X}")
    print(f"\ncmdline.txt entry:")
    print(f"  drm.edid_firmware=HDMI-A-1:edid_{profile_name}.bin")


if __name__ == '__main__':
    main()
