
from __future__ import print_function

from kwiver.vital.algo import ImageObjectDetector

from kwiver.vital.types import Image
from kwiver.vital.types import ImageContainer
from kwiver.vital.types import DetectedObject
from kwiver.vital.types import DetectedObjectSet
from kwiver.vital.types import DetectedObjectType
from kwiver.vital.types import BoundingBoxD

from vital.util.VitalPIL import get_pil_image

import numpy as np
import time
import os


class TFDetector( ImageObjectDetector ):
  """
  This detector uses tensorflow to generate object detections
  """
  # --------------------------------------------------------------------------
  def __init__(self):
    ImageObjectDetector.__init__(self)

    self.model_file = "model_file"
    self.norm_image_type = ""
    self.fixed_range = 7000
    self.confidence_thresh = 0.5
    self.memory_usage = 1.0
    self.category_name = "detection"

  def __del__(self):
    self.sess.close()

  # --------------------------------------------------------------------------
  def get_configuration(self):
    # Inherit from the base class
    cfg = super(ImageObjectDetector, self).get_configuration()

    cfg.set_value( "model_file", self.model_file )
    cfg.set_value( "norm_image_type", self.norm_image_type )
    cfg.set_value( "fixed_range", str( self.fixed_range ) )
    cfg.set_value( "confidence_thresh", str( self.confidence_thresh ) )
    cfg.set_value( "memory_usage", str( self.memory_usage ) )
    cfg.set_value( "category_name", self.category_name )

    return cfg

  def set_configuration( self, cfg_in ):
    cfg = self.get_configuration()
    cfg.merge_config( cfg_in )

    self.model_file = str(cfg.get_value("model_file"))
    self.norm_image_type = str(cfg.get_value("norm_image_type"))
    self.fixed_range = int(cfg.get_value("fixed_range"))
    self.confidence_thresh = float(cfg.get_value("confidence_thresh"))
    self.memory_usage = float(cfg.get_value("memory_usage"))
    self.category_name = str(cfg.get_value("category_name"))

    # Load detector
    import tensorflow as tf

    self.detection_graph = self.load_model(self.model_file)

    if self.memory_usage < 1.0:
      config = tf.ConfigProto()
      config.gpu_options.per_process_gpu_memory_fraction = self.memory_usage
      self.sess = tf.Session(graph=self.detection_graph, config=config)
    else:
      self.sess = tf.Session(graph=self.detection_graph)

  def check_configuration( self, cfg ):
    if not cfg.has_value( "model_file" ) or len( cfg.get_value("model_file")) == 0:
      print( "A network model file must be specified!" )
      return False
    return True

  # --------------------------------------------------------------------------
  def detect( self, in_img_c ):

    import tensorflow as tf
    import humanfriendly

    image_height = in_img_c.height(); image_width = in_img_c.width()

    if (self.norm_image_type and self.norm_image_type != "none"):
      print("Normalizing input image")

      in_img = in_img_c.image().asarray().astype("uint16")

      bottom, top = self.get_scaling_values(self.norm_image_type, in_img, image_height)
      in_img = self.lin_normalize_image(in_img, bottom, top)

      in_img = np.tile(in_img, (1,1,3))
    else:
      in_img = np.array(get_pil_image(in_img_c.image()).convert("RGB"))

    start_time = time.time()
    boxes, scores, classes = self.generate_detection(self.detection_graph, in_img)
    elapsed = time.time() - start_time
    print("Done running detector in {}".format(humanfriendly.format_timespan(elapsed)))

    good_boxes = []
    detections = DetectedObjectSet()

    for i in range(0, len(scores)):
       if(scores[i] >= self.confidence_thresh):
         bbox = boxes[i]
         good_boxes.append(bbox)

         top_rel = bbox[0]
         left_rel = bbox[1]
         bottom_rel = bbox[2]
         right_rel = bbox[3]
      
         xmin = left_rel * image_width
         ymin = top_rel * image_height
         xmax = right_rel * image_width
         ymax = bottom_rel * image_height

         dot = DetectedObjectType(self.category_name, scores[i])
         obj = DetectedObject(BoundingBoxD(xmin, ymin, xmax, ymax), scores[i], dot)
         detections.add(obj)

    print("Detected {}".format(len(good_boxes)))
    return detections

  def load_model(self, checkpoint):
    """
    Load a detection model (i.e., create a graph) from a .pb file
    """

    print("Creating Graph...")
    import tensorflow as tf

    detection_graph = tf.Graph()
    with detection_graph.as_default():
      od_graph_def = tf.GraphDef()
      with tf.gfile.GFile(checkpoint, "rb") as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name="")
    print("...done")

    return detection_graph

  def generate_detection(self, detection_graph, image_np):
    """
    boxes,scores,classes,images = generate_detection(detection_graph,image)

    Run an already-loaded detector network on an image.

    Boxes are returned in relative coordinates as (top, left, bottom, right); x,y origin is the upper-left.
    """

    image_np_expanded = np.expand_dims(image_np, axis=0)
    image_tensor = detection_graph.get_tensor_by_name("image_tensor:0")
    box = detection_graph.get_tensor_by_name("detection_boxes:0")
    score = detection_graph.get_tensor_by_name("detection_scores:0")
    clss = detection_graph.get_tensor_by_name("detection_classes:0")
    num_detections = detection_graph.get_tensor_by_name("num_detections:0")

    # Actual detection
    (box, score, clss, num_detections) = self.sess.run(
      [box, score, clss, num_detections],
      feed_dict={image_tensor: image_np_expanded})

    boxes = np.squeeze(np.array(box))
    scores = np.squeeze(np.array(score))
    classes = np.squeeze(np.array(clss)).astype(int)

    return boxes, scores, classes

  def lin_normalize_image(self, image_array, bottom=None, top=None):
    """Linear normalization for an image array
    Inputs:
      image_array: np.ndarray, image data to be normalized
      bit_8: boolean, if true outputs 8 bit, otherwise outputs 16 bit
      bottom: float, value to map to 0 in the new array
      top: float, value to map to 2^(bit_depth)-1 in the new array
    Output:
      scaled_image: nd.ndarray, scaled image between 0 and 2^(bit_depth) - 1
    """
    if bottom is None:
      bottom = np.min(image_array)
    if top is None:
      top = np.max(image_array)

    scaled_image = (image_array - bottom) / (top - bottom)
    scaled_image[scaled_image < 0] = 0
    scaled_image[scaled_image > 1] = 1
     
    scaled_image = np.floor(scaled_image * 255).astype(np.uint8)  # Map to [0, 2^8 - 1]

    return scaled_image
    
  def get_scaling_values(self, norm_method, in_img, num_rows):
    """Returns the bottom and top scaling parameters based on camera_pos
    Inputs:
      norm_method: string, name of camera pos or normalization method
      num_rows: int, number of rows in the image
    Outputs:
      bottom: int, number that maps to 0 in scaled image
      top: int, number that maps to 255 in scaled image
    """

    if norm_method == "none":
      bottom = 0
      top = 65535
    if norm_method == "adaptive_min_fixed_range":
      bottom = np.percentile( in_img, 1 )
      top = bottom + self.fixed_range
    elif norm_method == "P":
      if num_rows == 512:
        bottom = 53500
        top = 56500
      elif num_rows == 480:
        bottom = 50500
        top = 58500
      else:
        print("Unknown camera size for file %s" % filename)
    elif norm_method == "C":
      bottom = 50500
      top = 58500
    elif "," in norm_method:
      tokens = norm_method.rstrip().split(',')
      bottom = int(tokens[0])
      top = int(tokens[1])
    else:
      # camera_pos S and default
      bottom = 51000
      top = 57500
                  
    return bottom, top

def __vital_algorithm_register__():
  from kwiver.vital.algo import algorithm_factory

  # Register Algorithm
  implementation_name  = "tensorflow"

  if algorithm_factory.has_algorithm_impl_name(
      TFDetector.static_type_name(), implementation_name ):
    return

  algorithm_factory.add_algorithm( implementation_name,
  "Tensorflow detector testing routine", TFDetector )

  algorithm_factory.mark_algorithm_as_loaded( implementation_name )
