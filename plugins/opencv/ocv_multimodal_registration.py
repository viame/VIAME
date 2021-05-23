# Copyright (c) Microsoft Corporation. All rights reserved.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

from kwiver.sprokit.processes.kwiver_process import KwiverProcess
from kwiver.sprokit.pipeline import process

from kwiver.vital.types import Image
from kwiver.vital.types import ImageContainer
from kwiver.vital.types import F2FHomography

from PIL import Image as pil_image
from kwiver.vital.util.VitalPIL import get_pil_image, from_pil

import cv2
import csv
import numpy as np
import scipy.spatial

def compute_transform( optical, thermal, warp_mode = cv2.MOTION_HOMOGRAPHY,
  match_low_res=True, good_match_percent = 0.15, ratio_test = .85,
  match_height = 512, min_matches = 4, min_inliers = 4 ):
 
    # Convert images to grayscale    
    if len( thermal.shape ) == 3 and thermal.shape[2] == 3:
        thermal_gray = cv2.cvtColor( thermal, cv2.COLOR_RGB2GRAY )
    else:
        thermal_gray = thermal
 
    if len( optical.shape ) == 3 and optical.shape[2] == 3: 
        optical_gray = cv2.cvtColor( optical, cv2.COLOR_RGB2GRAY )
    else:
        optical_gray = optical

    # resize if requested
    if match_low_res:
        aspect = optical_gray.shape[1] / optical_gray.shape[0]
        optical_gray = cv2.resize( optical_gray, ( int( match_height*aspect ), match_height) )
    
    # Detect SIFT features and compute descriptors.
    sift = cv2.xfeatures2d.SIFT_create()

    keypoints1, descriptors1 = sift.detectAndCompute( thermal_gray, None )
    keypoints2, descriptors2 = sift.detectAndCompute( optical_gray, None )

    if len( keypoints1 ) < 2:
        print("not enough keypoints")
        return False, np.identity( 3 ), 0

    if len( keypoints2 ) < 2:
        print("not enough keypoints")
        return False, np.identity( 3 ), 0

    # scale feature points back to original size
    if match_low_res:
        scale = optical.shape[0] / optical_gray.shape[0]
        for i in range( 0, len( keypoints2 ) ):
            keypoints2[i].pt = ( keypoints2[i].pt[0]*scale, keypoints2[i].pt[1]*scale )
            
    # Pick good features
    if ratio_test < 1:
        # ratio test
        matcher = cv2.BFMatcher( cv2.NORM_L2, crossCheck=False )
        matches = matcher.knnMatch( descriptors1, descriptors2, k=2 )
   
        # Apply ratio test
        good_matches = []
        for m, n in matches:
            if m.distance < ratio_test * n.distance:
                good_matches.append( m )

        matches = good_matches
    else:
        # top percentage matches
        matcher = cv2.BFMatcher( cv2.NORM_L2, crossCheck=True )
        matches = matcher.match( descriptors1, descriptors2 )
   
        # Sort matches by score
        matches.sort( key=lambda x: x.distance, reverse=False )

        # Remove not so good matches
        num_good_matches = int( len( matches ) * good_match_percent )
        matches = matches[:num_good_matches]
   
    print( "%d matches" % len(matches) )

    if len( matches ) < min_matches:
        print( "not enough matches" )
        return False, np.identity( 3 ), 0

    # Extract location of good matches
    points1 = np.zeros( ( len( matches ), 2 ), dtype=np.float32 )
    points2 = np.zeros( ( len( matches ), 2 ), dtype=np.float32 )
 
    for i, match in enumerate( matches ):
        points1[ i, : ] = keypoints1[ match.queryIdx ].pt
        points2[ i, : ] = keypoints2[ match.trainIdx ].pt

    # Find homography
    h, mask = cv2.findHomography( points1, points2, cv2.RANSAC )
 
    print( "%d inliers" % sum( mask ) )

    if sum( mask ) < min_inliers:
        print( "not enough inliers" )
        return False, np.identity( 3 ), 0

    # Check if we have a robust set of inliers by computing the area of the convex hull
    
    # Good area is 11392
    try:
        print( 'Inlier area ', scipy.spatial.ConvexHull( points2[ np.isclose( mask.ravel(), 1 ) ] ).area )

        if scipy.spatial.ConvexHull( points2[ np.isclose( mask.ravel(), 1 ) ] ).area < 1000:
            print("Inliers seem colinear or too close, skipping")
            return False, np.identity(3), 0
    except:
        print( "Inliers seem colinear or too close, skipping" )
        return False, np.identity(3), 0

    # if non homography requested, compute from inliers
    if warp_mode != cv2.MOTION_HOMOGRAPHY:
        points1_inliers = []
        points2_inliers = []

        for i in range(0, len(mask)):
            if ( int(mask[i]) == 1):
                 points1_inliers.append( points1[i,:] )
                 points2_inliers.append( points2[i,:] )
             
        a = cv2.estimateRigidTransform( np.asarray( points1_inliers ), \
          np.asarray( points2_inliers ), ( warp_mode == cv2.MOTION_AFFINE ) )

        if a is None:
            return False, np.identity(3), 0

        h = np.identity(3)

        # turn in 3x3 transform
        h[0,:] = a[0,:]
        h[1,:] = a[1,:]

    return True, h, sum( mask )

# normlize thermal image
def normalize_thermal( thermal_image, percent=0.01 ):

    if not thermal_image is None and thermal_image.dtype is not np.dtype('uint8'):
        thermal_norm = np.floor( ( thermal_image -            \
          np.percentile( thermal_image, percent) ) /          \
            ( np.percentile( thermal_image, 100 - percent ) - \
              np.percentile( thermal_image, percent ) ) * 256 )
    else:
        thermal_norm = thermal_image

    return thermal_norm.astype( np.uint8 )

class register_frames_process( KwiverProcess ):
    """
    This process blanks out images which don't have detections on them.
    """
    # -------------------------------------------------------------------------
    def __init__( self, conf ):
        KwiverProcess.__init__( self, conf )

        # set up configs
        self.add_config_trait( "good_match_percent", "good_match_percent",
                               '0.15', 'Good match percent [0.0,1.0].' )
        self.add_config_trait( "ratio_test", "ratio_test",
                               '0.85', 'Feature point test ratio' )
        self.add_config_trait( "match_height", "match_height",
                               '512', 'Match height.' )
        self.add_config_trait( "min_matches", "min_matches",
                               '4', 'Minimum number of feature matches' )
        self.add_config_trait( "min_inliers", "min_inliers",
                               '4', 'Minimum number of inliers' )

        self.declare_config_using_trait( 'good_match_percent' )
        self.declare_config_using_trait( 'ratio_test' )
        self.declare_config_using_trait( 'match_height' )
        self.declare_config_using_trait( 'min_matches' )
        self.declare_config_using_trait( 'min_inliers' )

        # set up required flags
        optional = process.PortFlags()
        required = process.PortFlags()
        required.add( self.flag_required )

        # declare our ports (port-name, flags)
        self.add_port_trait( "optical_image", "image", "Input image" )
        self.add_port_trait( "thermal_image", "image", "Input image" )

        self.add_port_trait( "warped_optical_image", "image", "Output image" )
        self.add_port_trait( "warped_thermal_image", "image", "Output image" )
        self.add_port_trait( "optical_to_thermal_homog", "homography", "Output homog" )
        self.add_port_trait( "thermal_to_optical_homog", "homography", "Output homog" )

        self.declare_input_port_using_trait( 'optical_image', required )
        self.declare_input_port_using_trait( 'thermal_image', required )

        self.declare_output_port_using_trait( 'warped_optical_image', optional )
        self.declare_output_port_using_trait( 'warped_thermal_image', optional )
        self.declare_output_port_using_trait( 'optical_to_thermal_homog', optional )
        self.declare_output_port_using_trait( 'thermal_to_optical_homog', optional )

    # -------------------------------------------------------------------------
    def _configure( self ):
        self._base_configure()

        self._good_match_percent = float( self.config_value( 'good_match_percent' ) )
        self._ratio_test = float( self.config_value( 'ratio_test' ) )
        self._match_height = int( self.config_value( 'match_height' ) )
        self._min_matches = int( self.config_value( 'min_matches' ) )
        self._min_inliers = int( self.config_value( 'min_inliers' ) )

    # -------------------------------------------------------------------------
    def _step( self ):
        # grab image container from port using traits
        optical_c = self.grab_input_using_trait( 'optical_image' )
        thermal_c = self.grab_input_using_trait( 'thermal_image' )

        # Get python image from conatiner (just for show)
        optical_npy = optical_c.image().asarray().astype('uint8')
        thermal_npy = thermal_c.image().asarray().astype('uint16')

        thermal_norm = normalize_thermal( thermal_npy )

        if thermal_norm is not None and optical_npy is not None:
            # compute transform
            ret, transform, _ = compute_transform(
                optical_npy,
                thermal_norm,
                warp_mode = cv2.MOTION_HOMOGRAPHY,
                match_low_res = True,
                good_match_percent = self._good_match_percent,
                ratio_test = self._ratio_test,
                match_height = self._match_height,
                min_matches = self._min_matches,
                min_inliers = self._min_inliers )
        else:
           ret = False

        if ret:
            # TODO: Make all of these computations conditional on port connection
            inv_transform = np.linalg.inv( transform )

            thermal_warped = cv2.warpPerspective( thermal_npy, transform, \
              ( optical_npy.shape[1], optical_npy.shape[0] ) )
            optical_warped = cv2.warpPerspective( optical_npy, inv_transform, \
              ( thermal_npy.shape[1], thermal_npy.shape[0] ) )

            #self.push_to_port_using_trait( 'thermal_to_optical_homog',
            #   F2FHomography.from_matrix( transform, 'd' )
            #self.push_to_port_using_trait( 'optical_to_thermal_homog',
            #   F2FHomography.from_matrix( inv_transform, 'd' )

            self.push_to_port_using_trait( 'warped_thermal_image',
              ImageContainer.fromarray( thermal_warped ) )
            self.push_to_port_using_trait( 'warped_optical_image',
              ImageContainer.fromarray( optical_warped ) )
        else:
            print( 'alignment failed!' )

            #self.push_to_port_using_trait( "thermal_to_optical_homog", F2FHomography() )
            #self.push_to_port_using_trait( "optical_to_thermal_homog", F2FHomography() )

            self.push_to_port_using_trait( 'warped_optical_image', ImageContainer() )
            self.push_to_port_using_trait( 'warped_thermal_image', ImageContainer() )

        self._base_step()
