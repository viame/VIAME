#!/bin/sh

# Configurable Input Paths
export VIAME_INSTALL=/opt/noaa/viame

# Other paths generated from root
export VIAME_PIPELINES=${VIAME_INSTALL}/configs/pipelines/

# Remove utilities pipes which hold no meaning in web
rm -rf ${VIAME_PIPELINES}/*local*.pipe
rm -rf ${VIAME_PIPELINES}/*hough*.pipe
rm -rf ${VIAME_PIPELINES}/*_svm_models.pipe
rm -rf ${VIAME_PIPELINES}/detector_extract_chips.pipe

# Remove tracker pipelines which hold no meaning in web
rm -rf ${VIAME_PIPELINES}/tracker_short_term.pipe
rm -rf ${VIAME_PIPELINES}/tracker_stabilized_iou.pipe

# Remove seal and sea lion specialized pipelines un-runnable in web
rm -rf ${VIAME_PIPELINES}/detector_arctic_*fusion*.pipe
rm -rf ${VIAME_PIPELINES}/*2-cam.pipe
rm -rf ${VIAME_PIPELINES}/*3-cam.pipe
