#!/bin/bash
# -----------------------------------------------------------------------------
# Copyright (c) 2025-2026, VIDAL & ASTUDILLO Ltda and contributors.
# Author: JMVA, VIDAL & ASTUDILLO Ltda.
# www.vidalastudillo.com
# -----------------------------------------------------------------------------
#
# Script helper to use Buildroot containerized according to:
# https://github.com/vidalastudillo/docker-buildroot
#
# This specific implementation is for image production of:
CHIPSEE_PRODUCT_NAME="Chipsee PPC-CM4-101 (#CS12800RA4101P)"

# Provide usage instructions if no arguments have been provided
if [ "$#" -eq 0 ]; then
    echo "Utility to manage Buildroot on container to produce images for: $CHIPSEE_PRODUCT_NAME"
    echo "$0"
    echo "  def:      Set the configuration file - Equivalent to 'make chipsee_CS12800RA4101P_defconfig'"
    echo "  console:  Interactive shell inside the container"
    echo "  make ...: Standard Buildroot make commands"
    exit 0
fi

set -e

# Ensure the shared workspace volume exists
docker volume inspect buildroot_workspace >/dev/null 2>&1 || docker volume create buildroot_workspace

# --- Workspace & Storage ---
BUILDROOT_DIR=/root/buildroot
EXTERNAL_TREES_DIR=/buildroot_externals
OUTPUT_DIR=/workspace/outputs/chipsee/cs12800ra4101p
CCACHE_LIMIT="50G"

DEFAULT_CONFIG_NAME=chipsee_CS12800RA4101P_defconfig

# Detect if we are in an interactive terminal
[ -t 0 ] && TTY_FLAGS="-ti" || TTY_FLAGS=""

# At least on macOS, exposing the full OUTPUT_DIR to the host, seems to impact
# negatively the speed of the builds and frequent errors building libraries.
# That's why we just expose images and target
DOCKER_RUN="docker run
    --rm
    $TTY_FLAGS
    -v buildroot_workspace:/workspace
    -e OUTPUT_DIR=$OUTPUT_DIR
    -e BR2_CCACHE_DIR=/workspace/ccache
    -e BR2_DL_DIR=/workspace/dl
    -e CCACHE_MAXSIZE=$CCACHE_LIMIT
    -e CCACHE_BASEDIR=/workspace
    -e CCACHE_COMPILERCHECK=content
    -v $(pwd)/buildroot:$BUILDROOT_DIR
    -v $(pwd)/externals:$EXTERNAL_TREES_DIR
    -v $(pwd)/images/chipsee/cs12800ra4101p:$OUTPUT_DIR/images
    -v $(pwd)/target/chipsee/cs12800ra4101p:$OUTPUT_DIR/target
    -v $(pwd)/graphs/chipsee/cs12800ra4101p:$OUTPUT_DIR/graphs
    ${BUILDROOT_IMAGE:-va_buildroot}"

make() {
    echo "make BR2_EXTERNAL=${EXTERNAL_TREES_DIR}/chipsee O=$OUTPUT_DIR BR2_DL_DIR=/workspace/dl"
}

if [ "$1" == "def" ]; then
    eval $DOCKER_RUN $(make) $DEFAULT_CONFIG_NAME
elif [ "$1" == "make" ]; then
    eval $DOCKER_RUN $(make) ${@:2}
elif [ "$1" == "console" ]; then
    eval $DOCKER_RUN
fi
