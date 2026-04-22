# Buildroot External Tree: Chipsee

⚠️ **Status:** Under construction

External Buildroot tree for generating minimal Linux images to test Chipsee hardware and software.

## Target Platforms
- **CS10600RA4070P:** `chipsee_CS10600RA4070P_defconfig`

## Prerequisites
Host configured with [docker-buildroot](https://github.com/vidalastudillo/docker-buildroot).

## Build & Usage

**CRITICAL EXECUTION RULE (For Automation and Humans):** 
Due to Docker volume mounting (`$(pwd)`), all `run.sh` commands MUST be executed from the **root of the `docker-buildroot` project**, NOT from inside this external tree directory.

**CRITICAL BUILD RULE:** Avoid running `make clean` as full rebuilds take quite long. Rely on incremental builds.

### Build Workflow

```bash
# 1. Navigate to the project root
cd ../.. # Assuming you are in externals/chipsee/

# 2. Apply target configuration
./externals/chipsee/run.sh make chipsee_CS10600RA4070P_defconfig

# 3. Build the image
./externals/chipsee/run.sh make all
```

### Configuration Changes

Changes must be persisted in this repository, not in the Docker output directory.

- **Humans:** 
  1. Run `./externals/chipsee/run.sh make menuconfig` to modify settings interactively.
  2. Run `./externals/chipsee/run.sh make savedefconfig` to overwrite the target's defconfig in the repository (e.g., `configs/chipsee_CS10600RA4070P_defconfig`).
- **Automation/AI:** 
  DO NOT use `menuconfig` or rely on container-generated `.config` states. To persist configuration changes:
  1. Directly edit the source of truth: `externals/chipsee/configs/<target>_defconfig`.
  2. Directly modify or create `Config.in` and `*.mk` files within the `externals/chipsee/package/` structure.

## Development Conventions

- **Buildroot Targets:** Package names are case-sensitive. Always check `Config.in` and `*.mk` files to determine the exact name before executing rebuild commands (e.g., `make <pkg>-rebuild`).
- **Configuration Integrity:** Always synchronize `Config.in` selections with `.mk` dependencies.
- **Hardware Overlays:** Prioritize official hardware overlays (e.g., Raspberry Pi `config.txt`) over generic kernel command-line parameters (`cmdline.txt`).
- **Wrapper Logic:** All Buildroot commands must be executed through the provided `run.sh` script to ensure critical variables (like output directories `O=...`) are properly injected. Never run `make` directly.

## References
- [Buildroot Customization Manual](http://buildroot.uclibc.org/downloads/manual/manual.html#outside-br-custom)
