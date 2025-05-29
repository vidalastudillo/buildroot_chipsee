#!/bin/bash
# By JMVA, VIDAL & ASTUDILLO Ltda, 2025
#
# Script helper to use Buildroot containerized according to:
# https://github.com/vidalastudillo/docker-buildroot/tree/independent_buildroot
# However, this script provides options to perform the operations described
# on Quick Setup. Then only the git clone is required. 
#
# This specific implementation is for image production of:
CHIPSEE_PRODUCT_NAME="Chipsee PPC-CM4-070 (#CS10600RA4070P)"


# IMPORTANT: SECURITY WARNING!
# The container will access to the a .ssh folder on the host to be able to
# retrieve credentials for private repositories.


# Provide usage instructions if no arguments have been provided
if [ "$#" -eq 0 ]; then
    echo "Utility to manage Buildroot on container to produce images for: $CHIPSEE_PRODUCT_NAME"
    echo "$0"
    echo "  init:     Build Buildroot and Data containers"
    echo "  def:      Set the configuration file - Equivalent to 'make x__defconfig'"
    echo "  console:  Shell inside the Buildroot container"
    echo "  make ...: Usual 'make' commands used in Buildroot"
fi

ENVIRONMENT_FILE_PATH="$(dirname "$0")/.env"

# Check environment file exists
if test ! -f $ENVIRONMENT_FILE_PATH; then
  echo "$ENVIRONMENT_FILE_PATH File does not exist"
  echo "Please create one using as reference this one: $(dirname "$0")/.env_example"
  exit 0
fi

# Load environment variables
set -a; source $ENVIRONMENT_FILE_PATH; set +a

set -e  # From now on, exit immediately if a command exits with a non-zero status

# Board configuration to be used
DEFAULT_CONFIG_NAME=chipsee_CS10600RA4070P_defconfig

# Tag to identify the Buildroot container
CONTAINER_IMAGE_NAME=buidlroot_chipsee

# Tag to identify the Data container
CONTAINER_DATA_NAME=chipsee_cs10600ra4070p

# Folder name to be used to store the results
OUTPUT_SUBFOLDER_ON_HOST=CS07

# These are internal mappings for the containers, not meant to be changed
BUILDROOT_DIR=/root/buildroot
EXTERNALS_DIR=/buildroot_externals
OUTPUT_DIR=/buildroot_output


# At least on macOS, exposing the full OUTPUT_DIR to the host, seems to impact
# negatively the speed of the builds and frequent errors building libraries.
# That's why we just expose images and target

# Command to run the container linking volumes from the data container
DOCKER_RUN="docker run
    --rm
    -ti
    --volumes-from $CONTAINER_DATA_NAME
    -v $(pwd)/.ssh:/root/.ssh
    -v $(pwd)/buildroot:$BUILDROOT_DIR
    -v $(pwd)/externals:$EXTERNALS_DIR
    -v $(pwd)/images/$OUTPUT_SUBFOLDER_ON_HOST:$OUTPUT_DIR/images
    -v $(pwd)/target/$OUTPUT_SUBFOLDER_ON_HOST:$OUTPUT_DIR/target
    -v $(pwd)/graphs/$OUTPUT_SUBFOLDER_ON_HOST:$OUTPUT_DIR/graphs
    $CONTAINER_IMAGE_NAME"

# Command to build the shared Buildroot container
DOCKER_BUILD="docker build -t $CONTAINER_IMAGE_NAME:latest ."

# Command to build the data container for this particular product
DOCKER_CREATE_DATA_CONTAINER="docker run -i
    --name $CONTAINER_DATA_NAME $CONTAINER_IMAGE_NAME /bin/echo \"Data container for: $CONTAINER_DATA_NAME used by: $CONTAINER_IMAGE_NAME\""

# Docker run argument to be issued with every make command
argument_make() {
    echo "make BR2_EXTERNAL=$EXTERNALS_DIR/$EXTERNALS_SUBFOLDER_ON_HOST O=$OUTPUT_DIR "
}

# Docker run argument to set the default board configuration
argument_set_default_config_file() {
    echo "$DEFAULT_CONFIG_NAME"
}


if [ "$1" == "init" ]; then
    echo "Building container for Buildroot. Will be tagged: $CONTAINER_IMAGE_NAME"
    eval $DOCKER_BUILD
    echo "Init data container. Will be tagged: $CONTAINER_DATA_NAME"
    eval $DOCKER_CREATE_DATA_CONTAINER
elif [ "$1" == "def" ]; then
    eval $DOCKER_RUN $(argument_make) $(argument_set_default_config_file)
elif [ "$1" == "make" ]; then
    eval $DOCKER_RUN $(argument_make) ${@:2}
elif [ "$1" == "console" ]; then
    eval $DOCKER_RUN
# else
#     eval $DOCKER_RUN $@
fi
