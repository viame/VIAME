/*ckwg +29
 * Copyright 2017-2021 by Kitware, Inc.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 *  * Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 *  * Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 *  * Neither name of Kitware, Inc. nor the names of any contributors may be used
 *    to endorse or promote products derived from this software without specific
 *    prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <kwiversys/SystemTools.hxx>
#include <kwiversys/CommandLineArguments.hxx>

#include <vital/kwiver-include-paths.h>

#include <vital/plugin_loader/plugin_manager.h>
#include <vital/plugin_loader/plugin_factory.h>
#include <vital/config/config_block.h>
#include <vital/config/config_block_io.h>
#include <vital/util/demangle.h>
#include <vital/util/wrap_text_block.h>
#include <vital/algo/algorithm_factory.h>
#include <vital/algo/train_detector.h>
#include <vital/algo/detected_object_set_input.h>
#include <vital/algo/image_io.h>
#include <vital/types/image_container.h>
#include <vital/logger/logger.h>

#include <boost/filesystem.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/lexical_cast.hpp>

#include <sprokit/pipeline/process_exception.h>
#include <sprokit/processes/adapters/embedded_pipeline.h>
#include <sprokit/processes/adapters/adapter_types.h>

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>
#include <iterator>
#include <memory>
#include <map>
#include <cctype>
#include <regex>

// =======================================================================================
// Class storing all input parameters and private variables for tool
class trainer_vars
{
public:

  // Collected command line args
  kwiversys::CommandLineArguments m_args;

  // Config options
  bool opt_help;
  bool opt_list;
  bool opt_no_query;
  bool opt_no_adv_print;
  bool opt_no_emb_pipe;

  std::string opt_config;
  std::string opt_input_dir;
  std::string opt_input_list;
  std::string opt_input_truth;
  std::string opt_label_file;
  std::string opt_detector;
  std::string opt_out_config;
  std::string opt_threshold;
  std::string opt_settings;
  std::string opt_pipeline_file;
  std::string opt_frame_rate;

  trainer_vars()
  {
    opt_help = false;
    opt_list = false;
    opt_no_query = false;
    opt_no_adv_print = false;
    opt_no_emb_pipe = false;
  }

  virtual ~trainer_vars()
  {
  }
};

// =======================================================================================
// Define global variables used across this tool
static trainer_vars g_params;
static kwiver::vital::logger_handle_t g_logger;

typedef std::unique_ptr< kwiver::embedded_pipeline > pipeline_t;

// =======================================================================================
// Assorted filesystem related helper functions
bool does_file_exist( const std::string& location )
{
  return boost::filesystem::exists( location ) &&
         !boost::filesystem::is_directory( location );
}

bool does_folder_exist( const std::string& location )
{
  return boost::filesystem::exists( location ) &&
         boost::filesystem::is_directory( location );
}

bool list_all_subfolders( const std::string& location,
                          std::vector< std::string >& subfolders )
{
  subfolders.clear();

  if( !does_folder_exist( location ) )
  {
    return false;
  }

  boost::filesystem::path dir( location );

  for( boost::filesystem::directory_iterator dir_iter( dir );
       dir_iter != boost::filesystem::directory_iterator();
       ++dir_iter )
  {
    if( boost::filesystem::is_directory( *dir_iter ) )
    {
      subfolders.push_back( dir_iter->path().string() );
    }
  }

  return true;
}

bool list_files_in_folder( const std::string& location,
                           std::vector< std::string >& filepaths,
                           bool search_subfolders = false,
                           std::vector< std::string > extensions =
                             std::vector< std::string >() )
{
  filepaths.clear();

  if( !does_folder_exist( location ) )
  {
    return false;
  }

  boost::filesystem::path dir( location );

  for( boost::filesystem::directory_iterator file_iter( dir );
       file_iter != boost::filesystem::directory_iterator();
       ++file_iter )
  {
    if( boost::filesystem::is_regular_file( *file_iter ) )
    {
      if( extensions.empty() )
      {
        filepaths.push_back( file_iter->path().string() );
      }
      else
      {
        for( unsigned i = 0; i < extensions.size(); i++ )
        {
          if( file_iter->path().extension() == extensions[i] )
          {
            filepaths.push_back( file_iter->path().string() );
            break;
          }
        }
      }
    }
    else if( boost::filesystem::is_directory( *file_iter ) && search_subfolders )
    {
      std::vector< std::string > subfiles;
      list_files_in_folder( file_iter->path().string(),
        subfiles, search_subfolders, extensions );

      filepaths.insert( filepaths.end(), subfiles.begin(), subfiles.end() );
    }
  }

  return true;
}

bool create_folder( const std::string& location )
{
  boost::filesystem::path dir( location );

  if( !boost::filesystem::exists( dir ) )
  {
    return boost::filesystem::create_directories( dir );
  }

  return false;
}

std::string append_path( std::string p1, std::string p2 )
{
  return p1 + "/" + p2;
}

std::string get_filename_with_last_path( std::string path )
{
  return append_path( boost::filesystem::path( path ).parent_path().filename().string(),
                      boost::filesystem::path( path ).filename().string() );
}

std::string get_filename_no_path( std::string path )
{
  return boost::filesystem::path( path ).filename().string();
}

std::string add_quotes( const std::string& str )
{
  return "\"" + str + "\"";
}

bool ends_with_extension( const std::string& str, const std::string& ext )
{
  if( str.length() >= ext.length() )
  {
    return( 0 == str.compare( str.length() - ext.length(),
                              ext.length(), ext ) );
  }
  else
  {
    return false;
  }
}

bool ends_with_extension( const std::string& str,
                          const std::vector< std::string >& exts )
{
  for( auto ext : exts )
  {
    if( ends_with_extension( str, ext ) )
    {
      return true;
    }
  }
  return false;
}

template< typename T >
bool string_to_vector( const std::string& str,
                       std::vector< T >& out,
                       const std::string delims = "\n\t\v ," )
{
  out.clear();

  std::vector< std::string > parsed_string;

  boost::split( parsed_string, str,
                boost::is_any_of( delims ),
                boost::token_compress_on );

  try
  {
    for( std::string s : parsed_string )
    {
      if( !s.empty() )
      {
        out.push_back( boost::lexical_cast< T >( s ) );
      }
    }
  }
  catch( boost::bad_lexical_cast& )
  {
    return false;
  }

  return true;
}

template< typename T >
bool file_to_vector( const std::string& fn, std::vector< T >& out )
{
  std::ifstream in( fn.c_str() );
  out.clear();

  if( !in )
  {
    std::cerr << "Unable to open " << fn << std::endl;
    return false;
  }

  std::string line;
  while( std::getline( in, line ) )
  {
    if( !line.empty() )
    {
      out.push_back( boost::lexical_cast< T >( line ) );
    }
  }
  return true;
}

void correct_manual_annotations( kwiver::vital::detected_object_set_sptr dos )
{
  if( !dos )
  {
    return;
  }

  for( kwiver::vital::detected_object_sptr do_sptr : *dos )
  {
    if( do_sptr->confidence() < 0.0 )
    {
      do_sptr->set_confidence( 1.0 );
    }

    kwiver::vital::bounding_box_d do_box = do_sptr->bounding_box();

    if( do_box.min_x() > do_box.max_x() )
    {
      do_box = kwiver::vital::bounding_box_d(
        do_box.max_x(), do_box.min_y(), do_box.min_x(), do_box.max_y() );
    }
    if( do_box.min_y() > do_box.max_y() )
    {
      do_box = kwiver::vital::bounding_box_d(
        do_box.min_x(), do_box.max_y(), do_box.max_x(), do_box.min_y());
    }

    do_sptr->set_bounding_box( do_box );

    if( do_sptr->type() )
    {
      kwiver::vital::detected_object_type_sptr type_sptr = do_sptr->type();

      std::string top_category;
      double top_score;

      type_sptr->get_most_likely( top_category, top_score );

      if( top_score < 0.0 )
      {
        type_sptr->set_score( top_category, 1.0 );
        do_sptr->set_type( type_sptr );
      }
    }
  }
}

// =======================================================================================
// Assorted configuration related helper functions
static kwiver::vital::config_block_sptr default_config()
{
  kwiver::vital::config_block_sptr config
    = kwiver::vital::config_block::empty_config( "detector_trainer_tool" );

  config->set_value( "groundtruth_extensions", ".csv",
    "Groundtruth file extensions (csv, kw18, txt, etc...). Note: this is independent of "
    "the format that's stored in the file" );
  config->set_value( "groundtruth_style", "one_per_folder",
    "Can be either: \"one_per_file\" or \"one_per_folder\"" );
  config->set_value( "augmentation_pipeline", "",
    "Optional embedded pipeline for performing assorted augmentations" );
  config->set_value( "augmentation_cache", "augmented_images",
    "Directory to store augmented samples, a temp directiry is used if not specified." );
  config->set_value( "regenerate_cache", "true",
    "If an augmentation cache already exists, should we regenerate it or use it as-is?" );
  config->set_value( "augmented_ext_override", ".png",
    "Optional image extension over-ride for augmented images." );
  config->set_value( "default_percent_test", "0.05",
    "Percent [0.0, 1.0] of test samples to use if no manual files specified." );
  config->set_value( "test_burst_frame_count", "500",
    "Number of sequential frames to use in test set to avoid it being too similar to "
    "the training set." );
  config->set_value( "image_extensions",
    ".jpg;.jpeg;.JPG;.JPEG;.tif;.tiff;.TIF;.TIFF;.png;.PNG;.sgi;.SGI;.bmp;.BMP;.pgm;.PGM",
    "Semicolon list of seperated image extensions to use in training, images without "
    "this extension will not be included." );
  config->set_value( "video_extensions",
    ".mp4;.MP4;.mpg;.MPG;.mpeg;.MPEG;.avi;.AVI;.wmv;.WMV;.mov;.MOV;.webm;.WEBM;.ogg;.OGG",
    "Semicolon list of seperated video extensions to use in training, images without "
    "this extension will not be included." );
  config->set_value( "video_extractor", "ffmpeg",
    "Method to use to extract frames from video, can either be ffmpeg or a pipe file" );
  config->set_value( "frame_rate", "5",
    "Default frame rate to use for videos when it is not manually specified inside of a "
    "groundtruth file." );
  config->set_value( "threshold", "0.00",
    "Optional threshold to provide on top of input groundtruth. This is useful if the "
    "truth is derived from some automated detector and is unfiltered." );
  config->set_value( "check_override", "false",
    "Over-ride and ignore data safety checks." );
  config->set_value( "data_warning_file", "",
    "Optional file for storing possible data errors and warning." );

  kwiver::vital::algo::detected_object_set_input::get_nested_algo_configuration
    ( "groundtruth_reader", config, kwiver::vital::algo::detected_object_set_input_sptr() );
  kwiver::vital::algo::train_detector::get_nested_algo_configuration
    ( "detector_trainer", config, kwiver::vital::algo::train_detector_sptr() );

  return config;
}

static bool check_config( kwiver::vital::config_block_sptr config )
{
  if( !kwiver::vital::algo::detected_object_set_input::
        check_nested_algo_configuration( "groundtruth_reader", config ) )
  {
    return false;
  }

  if( !kwiver::vital::algo::train_detector::
        check_nested_algo_configuration( "detector_trainer", config ) )
  {
    return false;
  }

  return true;
}

pipeline_t load_embedded_pipeline( const std::string& pipeline_filename )
{
  std::unique_ptr< kwiver::embedded_pipeline > external_pipeline;

  if( !pipeline_filename.empty() )
  {
    auto dir = boost::filesystem::path( pipeline_filename ).parent_path();

    std::unique_ptr< kwiver::embedded_pipeline > new_pipeline =
      std::unique_ptr< kwiver::embedded_pipeline >( new kwiver::embedded_pipeline() );

    std::ifstream pipe_stream;
    pipe_stream.open( pipeline_filename, std::ifstream::in );

    if( !pipe_stream )
    {
      throw sprokit::invalid_configuration_exception( "viame_train_detector",
        "Unable to open pipeline file: " + pipeline_filename );
    }

    try
    {
      new_pipeline->build_pipeline( pipe_stream, dir.string() );
      new_pipeline->start();
    }
    catch( const std::exception& e )
    {
      throw sprokit::invalid_configuration_exception( "viame_train_detector",
                                                      e.what() );
    }

    external_pipeline = std::move( new_pipeline );
    pipe_stream.close();
  }

  return external_pipeline;
}

std::vector< std::string > extract_video_frames( const std::string& video_filename,
                                                 const std::string& pipeline_filename,
                                                 const double& frame_rate,
                                                 const std::string& output_directory,
                                                 bool skip_extract = false )
{
  std::cout << "Extracting frames from " << video_filename
            << " at rate " << frame_rate << std::endl;

  std::vector< std::string > output;

  std::string video_no_path = get_filename_no_path( video_filename );
  std::string output_dir = append_path( output_directory, video_no_path );
  std::string output_path = append_path( output_dir, "frame%06d.png" );
  std::string frame_rate_str = boost::lexical_cast< std::string >( frame_rate );

  if( !skip_extract )
  {
    if( does_folder_exist( output_dir ) )
    {
      boost::filesystem::remove_all( output_dir );
    }

    if( !create_folder( output_dir ) )
    {
      std::cout << "Error: Unable to create folder: " << output_dir << std::endl;
      return output;
    }
  }

  std::string cmd = "kwiver";

#ifdef WIN32
  cmd = cmd + ".exe";
#endif

  cmd = cmd + " runner " + add_quotes( pipeline_filename ) + " ";
  cmd = cmd + "-s input:video_filename=" + add_quotes( video_filename ) + " ";
  cmd = cmd + "-s input:video_reader:type=vidl_ffmpeg ";
  cmd = cmd + "-s input:target_frame_rate=" + frame_rate_str + " ";
  cmd = cmd + "-s output:file_name_template=" + add_quotes( output_path ) + " ";

  if( !skip_extract )
  {
    system( cmd.c_str() );
  }

  list_files_in_folder( output_dir, output );
  return output;
}

std::string replace_ext_with( std::string file_name, std::string ext )
{
  return file_name.substr( 0, file_name.find_last_of( '.' ) ) + ext;
}

std::string add_aux_ext( std::string file_name, unsigned id )
{
  std::size_t last_index = file_name.find_last_of( "." );
  std::string file_name_no_ext = file_name.substr( 0, last_index );
  std::string aux_addition = "_aux";

  if( id > 1 )
  {
    aux_addition += std::to_string( id );
  }

  return file_name_no_ext + aux_addition + file_name.substr( last_index );
}

bool file_contains_string( const std::string& file, std::string key )
{
  std::ifstream fin( file );
  while( !fin.eof() )
  {
    std::string line;
    std::getline( fin, line );

    if( line.find( key ) != std::string::npos )
    {
      fin.close();
      return true;
    }
  }
  fin.close();
  return false;
}

double get_file_frame_rate( const std::string& file )
{
  std::ifstream fin( file );

  if( !fin )
  {
    return -1.0;
  }

  std::string number;

  for( unsigned i = 0; i < 4 && !fin.eof(); i++ )
  {
    std::string line;
    std::getline( fin, line );

    if( line.size() > 5 && line[0] == '#' )
    {
      for( unsigned p = 0; p < line.size() - 4; p++ )
      {
        if( line.substr( p, 4 ) == "fps:" || line.substr( p, 4 ) == "fps=" )
        {
          for( unsigned l = p + 4; l < line.size(); l++ )
          {
            if( line[l] == ' ' )
            {
              continue;
            }
            else if( std::isdigit( line[l] ) || line[l] == '.' )
            {
              number = number + line[l];
            }
            else
            {
              break;
            }
          }
        }
      }
    }
  }

  fin.close();

  if( number.empty() )
  {
    return -1.0;
  }

  return std::stof( number );
}

bool load_file_list( const std::string& file, std::vector< std::string >& output )
{
  std::ifstream fin( file );
  output.clear();

  if( !fin )
  {
    return false;
  }

  while( !fin.eof() )
  {
    std::string line;
    std::getline( fin, line );
    output.push_back( line );
  }

  fin.close();
  return true;
}

bool run_pipeline_on_image( pipeline_t& pipe,
                            std::string pipe_file,
                            std::string input_name,
                            std::string output_name )
{
  kwiver::adapter::adapter_data_set_t ids =
    kwiver::adapter::adapter_data_set::create();

  ids->add_value( "input_file_name", input_name );

  ids->add_value( "output_file_name", output_name );

  if( file_contains_string( pipe_file, "output_file_name2" ) )
  {
    ids->add_value( "output_file_name2", add_aux_ext( output_name, 1 ) );
  }

  if( file_contains_string( pipe_file, "output_file_name3" ) )
  {
    ids->add_value( "output_file_name3", add_aux_ext( output_name, 2 ) );
  }

  pipe->send( ids );

  auto const& ods = pipe->receive();

  if( ods->is_end_of_data() )
  {
    throw std::runtime_error( "Pipeline terminated unexpectingly" );
  }

  auto const& success_flag = ods->find( "success_flag" );

  return success_flag->second->get_datum< bool >();;
}

std::string get_augmented_filename( std::string name,
                                    std::string subdir,
                                    std::string output_dir = "",
                                    std::string ext = ".png" )
{
  std::string parent_directory =
    kwiversys::SystemTools::GetParentDirectory( name );

  std::string file_name =
    kwiversys::SystemTools::GetFilenameName( name );

  std::size_t last_index = file_name.find_last_of( "." );
  std::string file_name_no_ext = file_name.substr( 0, last_index );

  std::vector< std::string > full_path;

  full_path.push_back( "" );

  if( output_dir.empty() )
  {
    full_path.push_back( boost::filesystem::temp_directory_path().string() );
  }
  else
  {
    full_path.push_back( output_dir );
  }

  full_path.push_back( subdir );
  full_path.push_back( file_name_no_ext + ext );

  std::string mod_path = kwiversys::SystemTools::JoinPath( full_path );
  return mod_path;
}

// =======================================================================================
/*                   _
 *   _ __ ___   __ _(_)_ __
 *  | '_ ` _ \ / _` | | '_ \
 *  | | | | | | (_| | | | | |
 *  |_| |_| |_|\__,_|_|_| |_|
 *
 */
int
main( int argc, char* argv[] )
{
  // Initialize shared storage
  g_logger = kwiver::vital::get_logger( "viame_train_detector" );

  // Parse options
  g_params.m_args.Initialize( argc, argv );
  g_params.m_args.StoreUnusedArguments( true );
  typedef kwiversys::CommandLineArguments argT;

  g_params.m_args.AddArgument( "--help",          argT::NO_ARGUMENT,
    &g_params.opt_help, "Display usage information" );
  g_params.m_args.AddArgument( "-h",              argT::NO_ARGUMENT,
    &g_params.opt_help, "Display usage information" );
  g_params.m_args.AddArgument( "--list",          argT::NO_ARGUMENT,
    &g_params.opt_list, "Display list of all trainable algorithms" );
  g_params.m_args.AddArgument( "-l",              argT::NO_ARGUMENT,
    &g_params.opt_list, "Display list of all trainable algorithms" );
  g_params.m_args.AddArgument( "--no-query",      argT::NO_ARGUMENT,
    &g_params.opt_no_query, "Do not query the user for anything" );
  g_params.m_args.AddArgument( "-nq",             argT::NO_ARGUMENT,
    &g_params.opt_no_query, "Do not query the user for anything" );
  g_params.m_args.AddArgument( "--no-adv-prints", argT::NO_ARGUMENT,
    &g_params.opt_no_adv_print, "Do not print out any advanced chars" );
  g_params.m_args.AddArgument( "-nap",            argT::NO_ARGUMENT,
    &g_params.opt_no_adv_print, "Do not print out any advanced chars" );
  g_params.m_args.AddArgument( "--no-embedded-pipe", argT::NO_ARGUMENT,
    &g_params.opt_no_emb_pipe, "Do not output embedded pipes" );
  g_params.m_args.AddArgument( "-nep",            argT::NO_ARGUMENT,
    &g_params.opt_no_emb_pipe, "Do not output embedded pipes" );
  g_params.m_args.AddArgument( "--config",        argT::SPACE_ARGUMENT,
    &g_params.opt_config, "Input configuration file with parameters" );
  g_params.m_args.AddArgument( "-c",              argT::SPACE_ARGUMENT,
    &g_params.opt_config, "Input configuration file with parameters" );
  g_params.m_args.AddArgument( "--input",         argT::SPACE_ARGUMENT,
    &g_params.opt_input_dir, "Input directory containing groundtruth" );
  g_params.m_args.AddArgument( "-i",              argT::SPACE_ARGUMENT,
    &g_params.opt_input_dir, "Input directory containing groundtruth" );
  g_params.m_args.AddArgument( "--input-list",    argT::SPACE_ARGUMENT,
    &g_params.opt_input_list, "Input list with data for training" );
  g_params.m_args.AddArgument( "-il",             argT::SPACE_ARGUMENT,
    &g_params.opt_input_list, "Input list with data for training" );
  g_params.m_args.AddArgument( "--input-truth",   argT::SPACE_ARGUMENT,
    &g_params.opt_input_truth, "Input list containing training truth" );
  g_params.m_args.AddArgument( "-it",             argT::SPACE_ARGUMENT,
    &g_params.opt_input_truth, "Input list containing training truth" );
  g_params.m_args.AddArgument( "--labels",        argT::SPACE_ARGUMENT,
    &g_params.opt_label_file, "Input label file for train categories" );
  g_params.m_args.AddArgument( "-lbl",            argT::SPACE_ARGUMENT,
    &g_params.opt_label_file, "Input label file for train categories" );
  g_params.m_args.AddArgument( "--detector",      argT::SPACE_ARGUMENT,
    &g_params.opt_detector, "Type of detector to train if no config" );
  g_params.m_args.AddArgument( "-d",              argT::SPACE_ARGUMENT,
    &g_params.opt_detector, "Type of detector to train if no config" );
  g_params.m_args.AddArgument( "--output-config", argT::SPACE_ARGUMENT,
    &g_params.opt_out_config, "Output a sample configuration to file" );
  g_params.m_args.AddArgument( "-o",              argT::SPACE_ARGUMENT,
    &g_params.opt_out_config, "Output a sample configuration to file" );
  g_params.m_args.AddArgument( "--setting",       argT::SPACE_ARGUMENT,
    &g_params.opt_settings, "Over-ride some setting in the config" );
  g_params.m_args.AddArgument( "-s",              argT::SPACE_ARGUMENT,
    &g_params.opt_settings, "Over-ride some setting in the config" );
  g_params.m_args.AddArgument( "--threshold",     argT::SPACE_ARGUMENT,
    &g_params.opt_threshold, "Threshold override to apply over input" );
  g_params.m_args.AddArgument( "-t",              argT::SPACE_ARGUMENT,
    &g_params.opt_threshold, "Threshold override to apply over input" );
  g_params.m_args.AddArgument( "--pipeline",      argT::SPACE_ARGUMENT,
    &g_params.opt_pipeline_file, "Pipeline file" );
  g_params.m_args.AddArgument( "-p",              argT::SPACE_ARGUMENT,
    &g_params.opt_pipeline_file, "Pipeline file" );
  g_params.m_args.AddArgument( "--default-vfr",   argT::SPACE_ARGUMENT,
    &g_params.opt_frame_rate, "Pipeline file" );
  g_params.m_args.AddArgument( "-vfr",            argT::SPACE_ARGUMENT,
    &g_params.opt_frame_rate, "Pipeline file" );

  // Parse args
  if( !g_params.m_args.Parse() )
  {
    std::cerr << "Problem parsing arguments" << std::endl;
    return EXIT_FAILURE;
  }

  // Print help
  if( argc == 1 || g_params.opt_help )
  {
    std::cout << "Usage: " << argv[0] << "[options]\n"
              << "\nTrain one of several object detectors in the system.\n"
              << g_params.m_args.GetHelp() << std::endl;
    return EXIT_FAILURE;
  }

  // List option
  if( g_params.opt_list )
  {
    kwiver::vital::plugin_manager& vpm = kwiver::vital::plugin_manager::instance();

    kwiver::vital::path_list_t pathl;
    const std::string& default_module_paths( DEFAULT_MODULE_PATHS );

    kwiversys::SystemTools::Split( default_module_paths, pathl, PATH_SEPARATOR_CHAR );

    for( auto path : pathl )
    {
      vpm.add_search_path( path );
    }

    vpm.load_plugins( pathl );

    auto fact_list = vpm.get_factories( "train_detector" );

    if( fact_list.empty() )
    {
      std::cerr << "No loaded detectors to list" << std::endl;
    }
    else
    {
      std::cout << std::endl << "Trainable detector variants:" << std::endl << std::endl;
    }

    for( auto fact : fact_list )
    {
      std::string name;
      if( fact->get_attribute( kwiver::vital::plugin_factory::PLUGIN_NAME, name ) )
      {
        std::cout << name << std::endl;
      }
    }
    return EXIT_FAILURE;
  }

  // Test for presence of two configs
  if( !g_params.opt_config.empty() && !g_params.opt_detector.empty() )
  {
    std::cerr << "Only one of --config and --detector allowed." << std::endl;
    return EXIT_FAILURE;
  }

  // Test for presence of two configs
  if( g_params.opt_config.empty() && g_params.opt_detector.empty() )
  {
    std::cerr << "One of --config and --detector must be set." << std::endl;
    return EXIT_FAILURE;
  }

  // Load KWIVER plugins
  kwiver::vital::plugin_manager::instance().load_all_plugins();
  kwiver::vital::config_block_sptr config = default_config();
  kwiver::vital::algo::detected_object_set_input_sptr groundtruth_reader;
  kwiver::vital::algo::train_detector_sptr detector_trainer;

  // Read all configuration options and check settings
  if( !g_params.opt_config.empty() )
  {
    try
    {
      config->merge_config( kwiver::vital::read_config_file( g_params.opt_config ) );
    }
    catch( const std::exception& e )
    {
      std::cerr << "Received exception: " << e.what() << std::endl
                << "Unable to load configuration file: "
                << g_params.opt_config << std::endl;

      return EXIT_FAILURE;
    }
  }
  else
  {
    config->set_value( "detector_trainer:type", g_params.opt_detector );
  }

  if( !g_params.opt_settings.empty() )
  {
    const std::string& setting = g_params.opt_settings;
    size_t const split_pos = setting.find( "=" );

    if( split_pos == std::string::npos )
    {
      std::string const reason = "Error: The setting on the command line \'"
        + setting + "\' does not contain the \'=\' string which separates "
        "the key from the value";

      throw std::runtime_error( reason );
    }

    kwiver::vital::config_block_key_t setting_key =
      setting.substr( 0, split_pos );
    kwiver::vital::config_block_value_t setting_value =
      setting.substr( split_pos + 1 );

    kwiver::vital::config_block_keys_t keys;

    kwiver::vital::tokenize( setting_key, keys,
      kwiver::vital::config_block::block_sep(),
      kwiver::vital::TokenizeTrimEmpty );

    if( keys.size() < 2 )
    {
      std::string const reason = "Error: The key portion of setting "
        "\'" + setting + "\' does not contain at least two keys in its "
        "keypath which is invalid. (e.g. must be at least a:b)";
  
      throw std::runtime_error( reason );
    }

    config->set_value( setting_key, setting_value );
  }

  if( g_params.opt_no_adv_print )
  {
    const std::string prefix1 = "detector_trainer:netharn";
    const std::string prefix2 = "detector_trainer:ocv_windowed:trainer:netharn";

    config->set_value( prefix1 + ":allow_unicode", "False" );
    config->set_value( prefix2 + ":allow_unicode", "False" );
  }

  if( g_params.opt_no_emb_pipe )
  {
    auto conf_values = config->available_values();

    for( auto conf : conf_values )
    {
      if( conf.find( "pipeline_template" ) != std::string::npos )
      {
        std::string new_value = std::regex_replace(
          config->get_value< std::string >( conf ),
          std::regex( "embedded_" ),
          "detector_" );

        config->set_value( conf, new_value );
      }
    }
  }

  kwiver::vital::algo::train_detector::set_nested_algo_configuration
    ( "detector_trainer", config, detector_trainer );
  kwiver::vital::algo::train_detector::get_nested_algo_configuration
    ( "detector_trainer", config, detector_trainer );

  kwiver::vital::algo::detected_object_set_input::set_nested_algo_configuration
    ( "groundtruth_reader", config, groundtruth_reader );
  kwiver::vital::algo::detected_object_set_input::get_nested_algo_configuration
    ( "groundtruth_reader", config, groundtruth_reader );

  bool valid_config = check_config( config );

  if( !g_params.opt_out_config.empty() )
  {
    write_config_file( config, g_params.opt_out_config );

    if( valid_config )
    {
      std::cout << "Configuration file contained valid parameters "
        "and may be used for running" << std::endl;
      return EXIT_SUCCESS;
    }
    else
    {
      std::cout << "Configuration deemed not valid." << std::endl;
      return EXIT_FAILURE;
    }
  }
  else if( !valid_config )
  {
    std::cout << "Configuration not valid." << std::endl;
    return EXIT_FAILURE;
  }

  // Read setup configs
  std::string groundtruth_exts_str =
    config->get_value< std::string >( "groundtruth_extensions" );
  std::string groundtruth_style =
    config->get_value< std::string >( "groundtruth_style" );
  std::string pipeline_file =
    config->get_value< std::string >( "augmentation_pipeline" );
  std::string augmented_cache =
    config->get_value< std::string >( "augmentation_cache" );
  bool regenerate_cache =
    config->get_value< bool >( "regenerate_cache" );
  std::string augmented_ext_override =
    config->get_value< std::string >( "augmented_ext_override" );
  double percent_test =
    config->get_value< double >( "default_percent_test" );
  unsigned test_burst_frame_count =
    config->get_value< double >( "test_burst_frame_count" );
  std::string image_exts_str =
    config->get_value< std::string >( "image_extensions" );
  std::string video_exts_str =
    config->get_value< std::string >( "video_extensions" );
  std::string video_extractor =
    config->get_value< std::string >( "video_extractor" );
  double frame_rate =
    config->get_value< double >( "frame_rate" );
  double threshold =
    config->get_value< double >( "threshold" );
  bool check_override =
    config->get_value< bool >( "check_override" );
  std::string data_warning_file =
    config->get_value< std::string >( "data_warning_file" );

  if( !g_params.opt_threshold.empty() )
  {
    threshold = atof( g_params.opt_threshold.c_str() );
    std::cout << "Using command line provided threshold: " << threshold << std::endl;
  }

  if( !g_params.opt_pipeline_file.empty() )
  {
    pipeline_file = g_params.opt_pipeline_file;
  }

  if( !augmented_cache.empty() &&
      !pipeline_file.empty() &&
      create_folder( augmented_cache ) )
  {
    regenerate_cache = true;
  }

  std::unique_ptr< std::ofstream > data_warning_writer;
  std::vector< std::string > mentioned_warnings;

  if( !data_warning_file.empty() )
  {
    data_warning_writer.reset( new std::ofstream( data_warning_file.c_str() ) );
  }

  if( !g_params.opt_frame_rate.empty() )
  {
    frame_rate = std::stod( g_params.opt_frame_rate );
  }

  std::vector< std::string > image_exts, video_exts, groundtruth_exts;
  bool one_file_per_image;

  if( groundtruth_style == "one_per_file" )
  {
    one_file_per_image = true;
  }
  else if( groundtruth_style == "one_per_folder" )
  {
    one_file_per_image = false;
  }
  else
  {
    std::cerr << "Invalid groundtruth style: " << groundtruth_style << std::endl;
    return EXIT_FAILURE;
  }

  if( percent_test < 0.0 || percent_test > 1.0 )
  {
    std::cerr << "Percent test must be [0.0,1.0]" << std::endl;
    return EXIT_FAILURE;
  }

  string_to_vector( image_exts_str, image_exts, "\n\t\v,; " );
  string_to_vector( video_exts_str, video_exts, "\n\t\v,; " );
  string_to_vector( groundtruth_exts_str, groundtruth_exts, "\n\t\v,; " );

  // Load labels.txt file
  std::string label_fn;

  if( !g_params.opt_label_file.empty() )
  {
    label_fn = g_params.opt_label_file;
  }
  else if( !g_params.opt_input_dir.empty() )
  {
    label_fn = append_path( g_params.opt_input_dir, "labels.txt" );
  }

  kwiver::vital::category_hierarchy_sptr model_labels;
  bool detection_without_label = false;

  if( !does_file_exist( label_fn ) && g_params.opt_out_config.empty() )
  {
    std::cout << "Label file (labels.txt) does not exist in input folder" << std::endl;
    std::cout << std::endl << "Would you like to train over all category labels? (y/n) ";

    if( !g_params.opt_no_query )
    {
      std::string response;
      std::cin >> response;

      if( response != "y" && response != "Y" && response != "yes" && response != "Yes" )
      {
        std::cout << std::endl << "Exiting training due to no labels.txt" << std::endl;
        return EXIT_FAILURE;
      }
    }
  }
  else if( g_params.opt_out_config.empty() )
  {
    try
    {
      model_labels.reset( new kwiver::vital::category_hierarchy( label_fn ) );
    }
    catch( const std::exception& e )
    {
      std::cerr << "Error reading labels.txt: " << e.what() << std::endl;
      return EXIT_FAILURE;
    }
  }

  // Data regardless of source - 
  std::vector< std::string > train_data;  // List of folders, image lists, or videos
  std::vector< std::string > train_truth; // Corresponding list of groundtruth files
  std::vector< std::string > test_items;  // A subset of train_data used for testing
  bool auto_detect_truth = false;         // Auto-detect truth if not manually specified

  // Option 1: a typical training data directory is input
  if( !g_params.opt_input_dir.empty() )
  {
    std::string input_dir = g_params.opt_input_dir;

    if( !does_folder_exist( input_dir ) && does_folder_exist( input_dir + ".lnk" ) )
    {
      input_dir = boost::filesystem::canonical(
        boost::filesystem::path( input_dir + ".lnk" ) ).string();
    }

    if( !does_folder_exist( input_dir ) && g_params.opt_out_config.empty() )
    {
      std::cerr << "Input directory does not exist, exiting." << std::endl;
      return EXIT_FAILURE;
    }

    // Load train.txt, if available
    const std::string train_fn = append_path( input_dir, "train.txt" );

    std::vector< std::string > train_files;
    if( does_file_exist( train_fn ) && !file_to_vector( train_fn, train_files ) )
    {
      std::cerr << "Unable to open " << train_fn << std::endl;
      return EXIT_FAILURE;
    }

    // Special use case for multiple overlapping streams
    const std::string train1_fn = append_path( input_dir, "train1.txt" );
    const std::string train2_fn = append_path( input_dir, "train2.txt" );

    if( does_file_exist( train1_fn ) )
    {
      if( does_file_exist( train_fn ) )
      {
        std::cerr << "Folder cannot contain both train.txt and train1.txt" << std::endl;
        return EXIT_FAILURE;
      }

      if( !file_to_vector( train1_fn, train_files ) )
      {
        std::cerr << "Unable to open " << label_fn << std::endl;
        return EXIT_FAILURE;
      }
    }

    std::vector< std::string > train2_files;
    if( does_file_exist( train2_fn ) && !file_to_vector( train2_fn, train2_files ) )
    {
      std::cerr << "Unable to open " << train2_fn << std::endl;
      return EXIT_FAILURE;
    }

    // Load test.txt, if available
    const std::string test_fn = append_path( input_dir, "test.txt" );

    std::vector< std::string > test_files;
    if( does_file_exist( test_fn ) && !file_to_vector( test_fn, test_files ) )
    {
      std::cerr << "Unable to open " << test_fn << std::endl;
      return EXIT_FAILURE;
    }

    // Append path to all test and train files, test to see if they all exist
    if( train_files.empty() && test_files.empty() )
    {
      std::cout << "Automatically selecting train and test files" << std::endl;
    }
    else if( train_files.empty() != test_files.empty() )
    {
      std::cerr << "If one of either train.txt or test.txt is specified, "
                << "then they must both be." << std::endl;
      return EXIT_FAILURE;
    }
    else
    {
      // Test first entry
      bool absolute_paths = false;
      std::string to_test = train_files[0];
      std::string full_path = append_path( g_params.opt_input_dir, to_test );

      if( !does_file_exist( full_path ) && does_file_exist( to_test ) )
      {
        absolute_paths = true;
        std::cout << "Using absolute paths in train.txt and test.txt" << std::endl;
      }

      for( unsigned i = 0; i < train_files.size(); i++ )
      {
        if( !absolute_paths )
        {
          train_files[i] = append_path( g_params.opt_input_dir, train_files[i] );
        }

        if( !does_file_exist( train_files[i] ) )
        {
          std::cerr << "Could not find train file: " << train_files[i] << std::endl;
        }
      }
      for( unsigned i = 0; i < test_files.size(); i++ )
      {
        if( !absolute_paths )
        {
          test_files[i] = append_path( g_params.opt_input_dir, test_files[i] );
        }

        if( !does_file_exist( test_files[i] ) )
        {
          std::cerr << "Could not find test file: " << test_files[i] << std::endl;
        }
      }
    }

    // Identify all sub-directories containing data
    std::vector< std::string > subfolders, videos;
    list_all_subfolders( g_params.opt_input_dir, subfolders );
    list_files_in_folder( g_params.opt_input_dir, videos, false, video_exts ); 
    train_data.insert( train_data.end(), subfolders.begin(), subfolders.end() );
    train_data.insert( train_data.end(), videos.begin(), videos.end() );

    if( train_data.empty() )
    {
      std::cout << "Error: training folder contains no sub-folders" << std::endl;
      return EXIT_FAILURE;
    }

    auto_detect_truth = true;
  }
  else if( !g_params.opt_input_list.empty() )
  {
    if( !does_file_exist( g_params.opt_input_list ) ||
        !load_file_list( g_params.opt_input_list, train_data ) )
    {
      std::cout << "Unable to load: " << g_params.opt_input_list << std::endl;
      return EXIT_FAILURE;
    }

    while( !train_data.empty() && train_data.back().empty() )
    {
      train_data.pop_back();
    }

    if( train_data.empty() )
    {
      std::cout << "Input training data list contains no entries" << std::endl;
      return EXIT_FAILURE;
    }

    auto_detect_truth = g_params.opt_input_truth.empty();

    if( !auto_detect_truth )
    {
      if( !does_file_exist( g_params.opt_input_truth ) ||
          !load_file_list( g_params.opt_input_truth, train_truth ) )
      {
        std::cout << "Unable to load: " << g_params.opt_input_truth << std::endl;
        return EXIT_FAILURE;
      }

      while( train_truth.size() > train_data.size() && train_truth.back().empty() )
      {
        train_truth.pop_back();
      }

      if( train_data.size() != train_truth.size() )
      {
        std::cout << "Training data and truth list lengths do not match" << std::endl;
        return EXIT_FAILURE;
      }
    }
  }

  // Load groundtruth for all image files in all folders using reader class
  std::vector< std::string > train_image_fn;
  std::vector< kwiver::vital::detected_object_set_sptr > train_gt;
  std::vector< std::string > test_image_fn;
  std::vector< kwiver::vital::detected_object_set_sptr > test_gt;

  // Retain class counts for error checking
  std::map< std::string, int > label_counts;

  for( unsigned i = 0; i < train_data.size(); i++ )
  {
    // Get next data entry to process
    const std::string& data_item = train_data[i];
    std::cout << "Processing " << data_item << std::endl;

    // Identify all truth files for this entry
    std::vector< std::string > image_files, gt_files;

    bool is_video = ends_with_extension( data_item, video_exts );

    if( is_video && auto_detect_truth )
    {
      std::string video_truth = replace_ext_with( data_item, groundtruth_exts[0] );

      if( !does_file_exist( video_truth ) )
      {
        std::cout << "Error: cannot find " << video_truth << std::endl;
        return EXIT_FAILURE;
      }

      gt_files.resize( 1, video_truth );
    }
    else if( !is_video && auto_detect_truth )
    {
      list_files_in_folder( data_item, gt_files, false, groundtruth_exts );
      std::sort( gt_files.begin(), gt_files.end() );

      if( one_file_per_image && ( image_files.size() != gt_files.size() ) )
      {
        std::cout << "Error: item " << data_item << " contains unequal truth and "
                  << "image file counts" << std::endl << " - Consider turning on "
                  << "the one_per_folder groundtruth style" << std::endl;
        return EXIT_FAILURE;
      }
      else if( gt_files.size() < 1 )
      {
        std::cout << "Error reading item " << data_item << ", no groundtruth." << std::endl;
        return EXIT_FAILURE;
      }
    }
    else
    {
      gt_files.resize( 1, train_truth[i] );
    }

    // Find images for this entry
    if( is_video )
    {
      double file_frame_rate = get_file_frame_rate( gt_files[0] );

      image_files = extract_video_frames( data_item, video_extractor,
        ( file_frame_rate > 0 ? file_frame_rate : frame_rate ),
        augmented_cache, !regenerate_cache );
    }
    else
    {
      list_files_in_folder( data_item, image_files, true, image_exts );
    }
    std::sort( image_files.begin(), image_files.end() );

    // Load groundtruth file for this entry
    kwiver::vital::algo::detected_object_set_input_sptr gt_reader;

    if( !one_file_per_image )
    {
      if( gt_files.size() != 1 )
      {
        std::cout << "Error: iten " << data_item
                  << " must contain only 1 groundtruth file" << std::endl;
        return EXIT_FAILURE;
      }

      kwiver::vital::algo::detected_object_set_input::set_nested_algo_configuration
        ( "groundtruth_reader", config, gt_reader );
      kwiver::vital::algo::detected_object_set_input::get_nested_algo_configuration
        ( "groundtruth_reader", config, gt_reader );

      std::cout << "Opening groundtruth file " << gt_files[0] << std::endl;

      gt_reader->open( gt_files[0] );
    }

    // Perform any augmentation for this entry, if enabled
    pipeline_t augmentation_pipe = load_embedded_pipeline( pipeline_file );
    std::string last_subdir;

    if( !augmented_cache.empty() && !pipeline_file.empty() )
    {
      std::vector< std::string > cache_path, split_folder;
      kwiversys::SystemTools::SplitPath( data_item, split_folder );
      last_subdir = ( split_folder.empty() ? data_item : split_folder.back() );

      cache_path.push_back( "" );
      cache_path.push_back( augmented_cache );
      cache_path.push_back( last_subdir );

      create_folder( kwiversys::SystemTools::JoinPath( cache_path ) );
    }

    // Read all images and detections in sequence
    if( image_files.size() == 0 )
    {
      std::cout << "Error: folder contains no image files." << std::endl;
    }

    for( unsigned i = 0; i < image_files.size(); ++i )
    {
      const std::string& image_file = image_files[i];

      bool use_image = true;
      std::string filtered_image_file;

      if( augmentation_pipe )
      {
        filtered_image_file = get_augmented_filename( image_file, last_subdir,
          augmented_cache, augmented_ext_override );

        if( regenerate_cache )
        {
          if( !run_pipeline_on_image( augmentation_pipe, pipeline_file,
                image_file, filtered_image_file ) )
          {
            use_image = false;
          }
        }
        else
        {
          use_image = boost::filesystem::exists( filtered_image_file );
        }
      }
      else
      {
        filtered_image_file = image_file;
      }

      // Read groundtruth for image
      kwiver::vital::detected_object_set_sptr frame_dets =
        std::make_shared< kwiver::vital::detected_object_set>();

      if( one_file_per_image )
      {
        gt_reader.reset();

        kwiver::vital::algo::detected_object_set_input::set_nested_algo_configuration
          ( "groundtruth_reader", config, gt_reader );
        kwiver::vital::algo::detected_object_set_input::get_nested_algo_configuration
          ( "groundtruth_reader", config, gt_reader );

        gt_reader->open( gt_files[i] );

        std::string read_fn = get_filename_no_path( image_file );

        gt_reader->read_set( frame_dets, read_fn );
        gt_reader->close();

        correct_manual_annotations( frame_dets );
      }
      else
      {
        std::string read_fn = get_filename_no_path( image_file );

        try
        {
          gt_reader->read_set( frame_dets, read_fn );

          correct_manual_annotations( frame_dets );
        }
        catch( const std::exception& e )
        {
          std::cerr << "Received exception: " << e.what() << std::endl
                    << "Unable to load groundtruth file: " << read_fn << std::endl;
          return EXIT_FAILURE;
        }
      }

      // Apply threshold to frame detections
      if( use_image )
      {
        std::cout << "Read " << frame_dets->size()
                  << " detections for "
                  << image_file << std::endl;

        kwiver::vital::detected_object_set_sptr filtered_dets =
          std::make_shared< kwiver::vital::detected_object_set>();

        for( auto det : *frame_dets )
        {
          bool add_detection = false;
          auto class_scores = det->type();

          if( class_scores )
          {
            for( auto gt_class : class_scores->class_names() )
            {
              if( !model_labels || model_labels->has_class_name( gt_class ) )
              {
                if( class_scores->score( gt_class ) >= threshold )
                {
                  if( model_labels )
                  {
                    gt_class = model_labels->get_class_name( gt_class );
                  }

                  label_counts[ gt_class ]++;
                  add_detection = true;
                }
              }
              else
              {
                class_scores->delete_score( gt_class );

                if( data_warning_writer &&
                    std::find(
                      mentioned_warnings.begin(),
                      mentioned_warnings.end(),
                      gt_class ) == mentioned_warnings.end() )
                {
                  *data_warning_writer << "Observed class: "
                    << gt_class << " not in input labels.txt" << std::endl;

                  mentioned_warnings.push_back( gt_class );
                }
              }
            }
          }
          else if( !model_labels || model_labels->size() == 1 )
          {
            add_detection = true; // single class problem, doesn't need dot
            detection_without_label = true; // at least 1 detection lacks a label
          }

          if( add_detection )
          {
            filtered_dets->add( det );
          }
        }

        train_image_fn.push_back( filtered_image_file );
        train_gt.push_back( filtered_dets );
      }
    }

    if( augmentation_pipe )
    {
      augmentation_pipe->send_end_of_input();
      augmentation_pipe->wait();
    }

    if( !one_file_per_image )
    {
      gt_reader->close();
    }
  }

  if( label_counts.empty() )
  {
    for( auto det_set : train_gt )
    {
      for( auto det : *det_set )
      {
        if( det->type() )
        {
          std::string gt_class;
          det->type()->get_most_likely( gt_class );

          if( !model_labels || model_labels->has_class_name( gt_class ) )
          {
            if( model_labels )
            {
              gt_class = model_labels->get_class_name( gt_class );
            }

            label_counts[ gt_class ]++;
          }
          else if( data_warning_writer &&
                  std::find(
                    mentioned_warnings.begin(),
                    mentioned_warnings.end(),
                    gt_class ) == mentioned_warnings.end() )
          {
            *data_warning_writer << "Observed class: "
               << gt_class << " not in input labels.txt" << std::endl;

            mentioned_warnings.push_back( gt_class );
          }
        }
      }
    }
  }

  if( label_counts.empty() ) // groundtruth has no classification labels
  {
    // Only 1 class, is okay but inject the classification into the groundtruth
    if( !model_labels || model_labels->size() == 1 )
    {
      std::string label = model_labels ? model_labels->all_class_names()[0] : "object";

      for( auto det_set : train_gt )
      {
        for( auto det : *det_set )
        {
          det->set_type(
            kwiver::vital::detected_object_type_sptr(
              new kwiver::vital::detected_object_type( label, 1.0 ) ) );

          label_counts[ label ]++;
        }
      }
      for( auto det_set : test_gt )
      {
        for( auto det : *det_set )
        {
          det->set_type(
            kwiver::vital::detected_object_type_sptr(
              new kwiver::vital::detected_object_type( label, 1.0 ) ) );
        }
      }
    }
    else // Not okay
    {
      std::cout << "Error: input labels.txt contains multiple classes, but supplied "
                << "truth files do not contain the training classes of interest, or "
                << "there was an error reading them from the input annotations."
                << std::endl;

      return EXIT_FAILURE;
    }
  }
  else if( !check_override && model_labels )
  {
    for( auto cls : model_labels->all_class_names() )
    {
      if( label_counts[ cls ] == 0 )
      {
        std::cout << "Error: no entries in groundtruth of class " << cls << std::endl
                  << std::endl
                  << "Optionally set \"check_override\" parameter to ignore this check."
                  << std::endl;

        return EXIT_FAILURE;
      }
    }
  }
  else if( detection_without_label )
  {
    std::cout << "Warning: one or more annotations contain no class label specified"
              << std::endl
              << "Consider checking your groundtruth for consisitency"
              << std::endl;
  }

  if( !model_labels )
  {
    model_labels.reset( new kwiver::vital::category_hierarchy() );

    for( auto label : label_counts )
    {
      model_labels->add_class( label.first );
    }
  }

  // Generate a testing and validation set automatically if enabled
  if( percent_test > 0.0 && test_image_fn.empty() )
  {
    unsigned total_images = train_image_fn.size();

    unsigned total_segment = static_cast< unsigned >( test_burst_frame_count / percent_test );
    unsigned train_segment = total_segment - test_burst_frame_count;

    if( total_images < total_segment )
    {
      total_segment = total_images;
      train_segment = total_images - static_cast< unsigned >( percent_test * total_images );

      if( total_segment > 1 && train_segment == total_segment )
      {
        train_segment = total_segment - 1;
      }
    }

    bool found_first = false, found_second = false, initial_override = false;
    std::vector< std::string > adj_train_image_fn;
    std::vector< kwiver::vital::detected_object_set_sptr > adj_train_gt;

    for( unsigned i = 0; i < train_image_fn.size(); ++i )
    {
      // First 2 conditionals are hack to ensure at least 1 truth frame
      // in both train and test sets, could be done better in future.
      if( !found_first && !train_gt[i]->empty() )
      {
        test_image_fn.push_back( train_image_fn[i] );
        test_gt.push_back( train_gt[i] );
        found_first = true;
      }
      else if( !found_second && !train_gt[i]->empty() )
      {
        adj_train_image_fn.push_back( train_image_fn[i] );
        adj_train_gt.push_back( train_gt[i] );
        found_second = true;
        initial_override = true;
      }
      else if( initial_override || i % total_segment < train_segment )
      {
        if( initial_override && i % total_segment == 0 )
        {
          initial_override = false;
        }
        adj_train_image_fn.push_back( train_image_fn[i] );
        adj_train_gt.push_back( train_gt[i] );
      }
      else
      {
        test_image_fn.push_back( train_image_fn[i] );
        test_gt.push_back( train_gt[i] );
      }
    }

    if( !found_first || !found_second )
    {
      std::cout << "Error: not enough data diversity to generate model" << std::endl;
      return EXIT_FAILURE;
    }

    train_image_fn = adj_train_image_fn;
    train_gt = adj_train_gt;
  }

  // Run training algorithm
  std::cout << "Beginning Training Process" << std::endl;
  std::string error;

  try
  {
    detector_trainer->add_data_from_disk( model_labels,
                                          train_image_fn, train_gt,
                                          test_image_fn, test_gt );

    detector_trainer->update_model();
  }
  catch( const std::exception& e )
  {
    error = e.what();
  }
  catch( const std::string& str )
  {
    error = str;
  }
  catch( ... )
  {
    error = "unknown fault";
  }

  if( !error.empty() )
  {
    if( error.find( "interupt_handler" ) != std::string::npos ||
        error.find( "KeyboardInterrupt" ) != std::string::npos )
    {
      std::cout << "Finished spooling down run after interrupt" << std::endl << std::endl;
    }
    else
    {
      std::cout << "Received exception: " << error << std::endl;
      std::cout << std::endl;
      std::cout << "Shutting down" << std::endl << std::endl;
    }
  }

  return EXIT_SUCCESS;
}
