===============================
Image Registration
===============================

This document corresponds to `this example online`_, in addition to the
image_registration example folder in a VIAME installation. This directory stores
assorted scripts for performing registration, either temporally across an image sequence
with a certain amount of overlap, or across modalities (e.g. optical and thermal
imagery).

.. _this example online: https://github.com/VIAME/VIAME/blob/master/examples/image_registration


******************
Build Requirements
******************

These are the build flags required to run this example, if building from the source.

In the pre-built binaries OpenCV is enabled by default, though not ITK which is required
for cross-modality registration.

| VIAME_ENABLE_OPENCV set to ON (optional)
| VIAME_ENABLE_ITK set to ON (optional)

********************
Code Used in Example
********************

| plugins/itk/
| plugins/opencv/

*****************
Mosaic generation
*****************

The ``generate_mosaic_for_list`` script shows the simplest way to
generate a mosaic.  The main program it invokes, ``create_mosaic.py``,
also supports additional options and functionality.

A basic invocation of ``create_mosaic.py`` is as follows (assuming
``setup_viame.sh`` or ``setup_viame.bat`` has been run)::

  create_mosaic.py --step 1 mosaic.jpg homographies.txt image_list.txt

This generates a mosaic image named ``mosaic.jpg`` from a file
containing homographies, here ``homographies.txt``, and a file listing
images, one per line, here ``image_list.txt``.  The homography file
can be generated using one of the stabilization pipelines, as is done
in the ``generate_mosaic_for_list`` script.

The ``--step`` option controls what fraction of the input frames are
drawn in the output.  ``--step 1``, as above, will draw every frame,
``--step 2`` will draw every other frame, ``--step 3`` will draw every
third frame, and so on.  Drawing fewer frames will make the process go
faster, but drawing too few frames can create gaps.

Three other options are available for frame selection.  ``--frames N``
draws *N* regularly spaced frames.  For example, ``--frames 2`` would
only draw the first and last frame while ``--frames 3`` would also
draw the middle frame.  Either ``--step`` or ``--frames`` must be
used, but not both.  ``--start`` and ``--stop`` can be used,
individually or together, to draw only frames from a particular range.
For example, with ``--start 3 --stop 8``, only frames 3, 4, 5, 6, and
7 will be considered.  Note that frames are counted starting from 0
and that the value passed to ``--stop`` is excluded.  ``--step`` and
``--frames`` are considered relative to any range specified using
``--start`` and ``--stop``.  ``--start`` and ``--stop`` are necessary
when a homography sequence has a "break" where the reference frame
(the last number of each line in a homography file) changes; all
selected frames must have the same reference frame.

Here are some examples of how the frame selections options affect
which frames are drawn from a 10-frame sequence:

- ``--step 1``: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
- ``--step 2``: 0, 2, 4, 6, 8
- ``--frames 2``: 0, 9
- ``--frames 4``: 0, 3, 6, 9
- ``--start 3``: 3, 4, 5, 6, 7, 8, 9
- ``--stop 8``: 0, 1, 2, 3, 4, 5, 6, 7
- ``--start 3 --stop 8``: 3, 4, 5, 6, 7
- ``--start 3 --step 2``: 3, 5, 7, 9
- ``--start 3 --frames 4``: 3, 5, 7, 9

Several options control the drawing process itself.  ``--zoom Z``
scales the output image by a factor of *Z*.  For example, if after
some invocation ``create_mosaic.py mosaic.jpg ...``, ``mosaic.jpg``
would be 20,000 x 10,000 pixels, then ``create_mosaic.py -Z 0.25
mosaic.jpg ...`` would result in ``mosaic.jpg`` being approximately
5,000 x 2,500 pixels (it might not be exactly that due to rounding of
image sizes).  If the full-resolution image is not needed, then
passing a value less than 1 will reduce memory consumption and also
make the creation process faster.

The ``--reverse`` option will draw the images in the opposite of their
usual order.  Normally, later frames are drawn on top of earlier ones.
With ``--reverse``, the initial frames will be on top instead.
Generating two versions of a mosaic, one using ``--reverse`` and the
other not, can be useful in evaluating how well the homographies align
the images.

The last option, ``--optimize-fit``, applies an extra homography to
the output that, when combined with each selected homography, attempts
to minimize the overall distortion of the images in the output,
keeping them near their original size and shape.  Without this option,
aside from the limited effects of ``--zoom``, images are transformed
exactly as described in the input homography file, except for a global
translation to keep the rendered mosaic in bounds.  This option is not
guaranteed to always compute the same transformation for a given
input, but in practice the result is usually indistinguishable.

If you have coregistered image sequences, e.g. from a multi-camera
platform, ``create_mosaic.py`` can also handle that.  The basic form
is::

  create_mosaic.py --step 1 mosaic.jpg homogs1.txt images1.txt homogs2.txt images2.txt

That is, the homography files and image lists associated with
additional sequences are added in alternating fashion.  Appropriate
homography files are for instance produced by the
``suppressor_sea_lion_3-cam`` pipeline, or anything using
``many_image_stabilizer``.  All the previous options still apply, but
note that frame selection applies individually to each sequence.  Thus
passing ``--step 2 --stop 6`` instead of ``--step 1`` above would draw
images 0, 2, and 4 from the first sequence as well as images 0, 2, and
4 from the second sequence.  The order of drawing in this case is
(sequence 1) 0, (sequence 2) 0, (sequence 1) 2, (sequence 2) 2,
(sequence 1) 4, (sequence 2) 4.
