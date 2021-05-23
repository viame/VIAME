#!/bin/sh

# Setup VIAME Paths (no need to run multiple times if you already ran it)

export VIAME_INSTALL="$(cd "$(dirname ${BASH_SOURCE[0]})" && pwd)/../.."
export INPUT_IMAGE_PATTERN=/path/to/images/*.png

source ${VIAME_INSTALL}/setup_viame.sh 

export KWIVER_DEFAULT_LOG_LEVEL=error

# Run pipelines

ls ${INPUT_IMAGE_PATTERN} > input_list.txt

kwiver runner ${VIAME_INSTALL}/configs/pipelines/register_using_homographies.pipe \
              -s input:video_filename=input_list.txt

python ${VIAME_INSTALL}/configs/create_mosaic.py first_mosaic.png output-homog.txt input_list.txt --step 1
