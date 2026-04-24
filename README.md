# Buildroot External Tree: Chipsee

⚠️ **Status:** Under construction

External Buildroot tree for generating minimal Linux images to test [Chipsee Raspberry Pi based hardware](https://chipsee.com/product-category/ipc/arm-ipc/arm-raspberry-pi/) and software.

## Target Platforms
- **CS10600RA4070P:** `chipsee_CS10600RA4070P_defconfig`

## Prerequisites

Either:
1. `Buildroot` and this repo installed as an external customization for it (See `References` below).
2. Host configured with [docker-buildroot](https://github.com/vidalastudillo/docker-buildroot).

## Build & Usage

### For the **first option** above

Typical workflow:

```
# Set configuration, i.e.
make chipsee_CS10600RA4070P_defconfig

# Customize
 make menuconfig

# To overwrite the target's defconfig in the repository (e.g., `configs/chipsee_CS10600RA4070P_defconfig`).
make savedefconfig

# Build the image
./externals/chipsee/run.sh make all
```

### For the **second option** above

When using the container infrastructure referenced, there is a convenient script `run.sh` to perform operations inside the containers. Running without any parameters displays its usage details.

Currently hardcoded for `CS10600RA4070P`.

**Important:** 

- **Wrapper Logic:** All Buildroot commands must be executed through the provided `run.sh` script to ensure critical variables (like output directories `O=...`) are properly injected. Never run `make` directly.
- **Running the helper script** Due to Docker volume mounting (`$(pwd)`), all `run.sh` commands MUST be executed from the **root of the `docker-buildroot` project**, NOT from inside this external tree directory.

Then, its workflow would be something like:

```bash
# 1. Navigate to the project root
cd ../.. # Assuming you are in externals/chipsee/

# 2. Apply target configuration
./externals/chipsee/run.sh make chipsee_CS10600RA4070P_defconfig

# 3. Build the image
./externals/chipsee/run.sh make all
```

## CS10600RA4070P — Display Pipeline

The CS10600RA4070P routes CM4 HDMI output through an HDMI-to-DPI bridge chip to a 7" 1024×600 panel. Three non-obvious configurations are required that differ from a standard HDMI display.

### Full KMS (`vc4-kms-v3d`)

Chipsee's reference images use `vc4-fkms-v3d` on kernel 5.15. This tree targets kernel 6.12 with Full KMS (`vc4-kms-v3d`). Relevant `config.txt` parameters:

- `dtoverlay=vc4-kms-v3d` — Full KMS driver
- `disable_fw_kms_setup=1` — prevents the firmware from appending its own `video=` to `cmdline.txt`; under Full KMS the DRM driver owns mode-setting entirely
- `hdmi_force_hotplug=1` — required because the bridge has no HPD line
- `hdmi_timings` / `hdmi_group` / `hdmi_mode` are firmware-only parameters silently ignored under Full KMS; display timing is provided exclusively via the synthetic EDID

### Synthetic EDID

The HDMI-to-DPI bridge has no DDC EEPROM, so the kernel cannot negotiate resolution or colorspace with the display. `board/gen_edid.py` generates a synthetic EDID 1.3 binary from the manufacturer timing parameters. The binary is produced at build time by the `chipsee-display` package and injected at boot via `cmdline.txt`:

```
drm.edid_firmware=HDMI-A-1:edid_cs10600ra4070.bin
```

The EDID includes a CEA-861 extension block with the HDMI Licensing LLC VSDB (OUI `0x000C03`). This causes `drm_detect_hdmi_monitor()` to return `true`, which makes `vc4` send AVI infoframes with `colorspace=RGB` on every frame. Without it, the driver treats the sink as DVI, sends no infoframe, and the bridge defaults to YCbCr — producing severe color corruption (cyan instead of red, purple background).

`gen_edid.py` can also be used standalone during development:

```bash
python3 board/gen_edid.py --list          # show available profiles
python3 board/gen_edid.py cs10600ra4070   # write binary to rootfs_overlay/lib/firmware/
```

### Color Quantization Range

The bridge chip expects RGB limited range (16–235), consistent with Chipsee's reference firmware (`hdmi_pixel_encoding=1`). Under Full KMS with `broadcast_rgb=Automatic`, `vc4` sends full range (0–255) for non-CEA modes, causing washed-out colors and a black-on-black console.

The `chipsee-display` package compiles `broadcast-rgb` from source and installs the init script `/etc/init.d/S20broadcast_rgb`, which runs it at boot. `broadcast-rgb` sets the DRM connector property `Broadcast RGB = 2` (Limited 16:235) via `DRM_IOCTL_MODE_SETPROPERTY` before any DRM client acquires master.

## Custom Packages

| Package | Kconfig | Purpose |
|---------|---------|---------|
| `chipsee-display` | `BR2_PACKAGE_CHIPSEE_DISPLAY` | Synthetic EDID + `broadcast-rgb` for Chipsee HDMI-to-DPI panels. Select the display model via `BR2_PACKAGE_CHIPSEE_DISPLAY_<MODEL>`. |
| `testing-kmscube` | `BR2_PACKAGE_TESTING_KMSCUBE` | Selects `kmscube` for display testing. |
| `testing-utilities` | `BR2_PACKAGE_BASIC_TESTING_UTILITIES` | Development bundle: DHCP, SSH (Dropbear), nano, neofetch, lshw, edid-decode. |

## Development Conventions

- **Buildroot Targets:** Package names are case-sensitive. Always check `Config.in` and `*.mk` files to determine the exact name before executing rebuild commands (e.g., `make <pkg>-rebuild`).
- **Configuration Integrity:** Always synchronize `Config.in` selections with `.mk` dependencies.
- **Hardware Overlays:** Prioritize official hardware overlays (e.g., Raspberry Pi `config.txt`) over generic kernel command-line parameters (`cmdline.txt`).

## References

- [Buildroot Customization Manual](http://buildroot.uclibc.org/downloads/manual/manual.html#outside-br-custom)
