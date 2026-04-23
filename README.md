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

## Development Conventions

- **Buildroot Targets:** Package names are case-sensitive. Always check `Config.in` and `*.mk` files to determine the exact name before executing rebuild commands (e.g., `make <pkg>-rebuild`).
- **Configuration Integrity:** Always synchronize `Config.in` selections with `.mk` dependencies.
- **Hardware Overlays:** Prioritize official hardware overlays (e.g., Raspberry Pi `config.txt`) over generic kernel command-line parameters (`cmdline.txt`).

## References

- [Buildroot Customization Manual](http://buildroot.uclibc.org/downloads/manual/manual.html#outside-br-custom)
