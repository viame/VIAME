/*ckwg +29
 * Copyright 2017-2020 by Kitware, Inc.
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
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
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

/**
 * \file
 * \brief Implementation of read_object_track_set_viame_csv
 */

#include "read_object_track_set_viame_csv.h"
#include "filename_to_timestamp.h"
#include "notes_to_attributes.h"

#include <vital/util/tokenize.h>
#include <vital/util/data_stream_reader.h>

#include <kwiversys/SystemTools.hxx>

namespace viame {

enum
{
  COL_DET_ID=0,  // 0: Object ID
  COL_SOURCE_ID, // 1
  COL_FRAME_ID,  // 2
  COL_MIN_X,     // 3
  COL_MIN_Y,     // 4
  COL_MAX_X,     // 5
  COL_MAX_Y,     // 6
  COL_CONFIDENCE,// 7
  COL_LENGTH,    // 8
  COL_TOT        // 9
};

// -------------------------------------------------------------------------------
class read_object_track_set_viame_csv::priv
{
public:
  priv( read_object_track_set_viame_csv* parent )
    : m_parent( parent )
    , m_logger( kwiver::vital::get_logger( "read_object_track_set_viame_csv" ) )
    , m_batch_load( true )
    , m_delim( "," )
    , m_confidence_override( -1.0 )
    , m_frame_id_adjustment( 0 )
    , m_first( true )
    , m_current_idx( 0 )
    , m_last_idx( 1 )
  {}

  ~priv() {}

  read_object_track_set_viame_csv* m_parent;
  kwiver::vital::logger_handle_t m_logger;
  typedef int frame_id_t;

  // Configuration parameters
  bool m_batch_load;
  std::string m_delim;
  double m_confidence_override;
  frame_id_t m_frame_id_adjustment;

  // Internal counters
  bool m_first;
  frame_id_t m_current_idx;
  frame_id_t m_last_idx;

  void read_all();

  typedef std::vector< kwiver::vital::track_sptr > track_vector;

  // Map of object tracks indexed by frame number. Each set contains all tracks
  // referenced (active) on that individual frame.
  std::map< frame_id_t, track_vector > m_tracks_by_frame_id;

  // Compilation of all loaded tracks, track id -> track sptr mapping
  std::map< frame_id_t, kwiver::vital::track_sptr > m_all_tracks;

  // Compilation of all loaded track IDs, track id -> type string
  std::map< frame_id_t, std::string > m_track_ids;
};


// ===============================================================================
read_object_track_set_viame_csv
::read_object_track_set_viame_csv()
  : d( new read_object_track_set_viame_csv::priv( this ) )
{
}


read_object_track_set_viame_csv
::~read_object_track_set_viame_csv()
{
}


// -------------------------------------------------------------------------------
void
read_object_track_set_viame_csv
::open( std::string const& filename )
{
  kwiver::vital::algo::read_object_track_set::open( filename );

  d->m_first = true;

  d->m_tracks_by_frame_id.clear();
  d->m_all_tracks.clear();
  d->m_track_ids.clear();
}


// -------------------------------------------------------------------------------
void
read_object_track_set_viame_csv
::set_configuration( kwiver::vital::config_block_sptr config )
{
  d->m_delim =
    config->get_value< std::string >( "delimiter", d->m_delim );
  d->m_batch_load =
    config->get_value< bool >( "batch_load", d->m_batch_load );
  d->m_confidence_override =
    config->get_value< double >( "confidence_override", d->m_confidence_override );
  d->m_frame_id_adjustment =
    config->get_value< int >( "frame_id_adjustment", d->m_frame_id_adjustment );

  d->m_current_idx = d->m_frame_id_adjustment;
}


// -------------------------------------------------------------------------------
bool
read_object_track_set_viame_csv
::check_configuration( kwiver::vital::config_block_sptr config ) const
{
  return true;
}


// -------------------------------------------------------------------------------
bool
read_object_track_set_viame_csv
::read_set( kwiver::vital::object_track_set_sptr& set )
{
  bool was_first = d->m_first;

  if( was_first )
  {
    // Read in all detections
    d->read_all();
    d->m_first = false;
  }

  if( d->m_batch_load )
  {
    if( !was_first )
    {
      return false;
    }
    std::vector< kwiver::vital::track_sptr > trks;

    for( auto it = d->m_all_tracks.begin(); it != d->m_all_tracks.end(); ++it )
    {
      trks.push_back( it->second );
    }

    set = kwiver::vital::object_track_set_sptr(
      new kwiver::vital::object_track_set( trks ) );

    return true;
  }

  if( d->m_current_idx > d->m_last_idx )
  {
    return false;
  }

  // Return detection set at current index if there is one
  if( d->m_tracks_by_frame_id.count( d->m_current_idx ) == 0 )
  {
    // Return empty set
    set = std::make_shared< kwiver::vital::object_track_set>();
  }
  else
  {
    // Return tracks for this frame
    kwiver::vital::object_track_set_sptr new_set(
      new kwiver::vital::object_track_set(
        d->m_tracks_by_frame_id[ d->m_current_idx ] ) );

    set = new_set;
  }

  ++d->m_current_idx;

  return true;
}


// -------------------------------------------------------------------------------
void
read_object_track_set_viame_csv::priv
::read_all()
{
  std::string line;
  kwiver::vital::data_stream_reader stream_reader( m_parent->stream() );

  m_tracks_by_frame_id.clear();
  m_all_tracks.clear();
  m_track_ids.clear();

  // Read track file
  while( stream_reader.getline( line ) )
  {
    if( !line.empty() && line[0] == '#' )
    {
      continue;
    }

    std::vector< std::string > col;
    kwiver::vital::tokenize( line, col, m_delim, false );

    if( col.size() < 9 )
    {
      std::stringstream str;
      str << "This is not a viame_csv file; found " << col.size()
          << " columns in\n\"" << line << "\"";
      throw kwiver::vital::invalid_data( str.str() );
    }

    /*
     * Check to see if we have seen this frame before. If we have,
     * then retrieve the frame's index into our output map. If not
     * seen before, add frame -> detection set index to our map and
     * press on.
     *
     * This allows for track states to be written in a non-contiguous
     * manner as may be done by streaming writers.
     */
    int trk_id = atoi( col[COL_DET_ID].c_str() );
    frame_id_t frame_id = atoi( col[COL_FRAME_ID].c_str() );
    frame_id = frame_id + m_frame_id_adjustment;
    kwiver::vital::time_usec_t frame_time;
    std::string str_id = col[COL_SOURCE_ID];

    kwiver::vital::bounding_box_d bbox(
      atof( col[COL_MIN_X].c_str() ),
      atof( col[COL_MIN_Y].c_str() ),
      atof( col[COL_MAX_X].c_str() ),
      atof( col[COL_MAX_Y].c_str() ) );

    double conf = atof( col[COL_CONFIDENCE].c_str() );

    if( m_confidence_override > 0.0 )
    {
      conf = m_confidence_override;
    }

    // Create detection object
    kwiver::vital::detected_object_sptr dob;

    kwiver::vital::detected_object_type_sptr dot =
      std::make_shared<kwiver::vital::detected_object_type>();

    bool found_attribute = false;

    for( unsigned i = COL_TOT; i < col.size(); i+=2 )
    {
      if( col[i].empty() || col[i][0] == '(' )
      {
        found_attribute = true;
        break;
      }

      if( col.size() < i + 2 )
      {
        std::stringstream str;
        str << "Every species pair must contain a confidence; error "
            << "at\n\"" << line << "\"";
        throw kwiver::vital::invalid_data( str.str() );
      }

      std::string spec_id = col[i];
      double spec_conf = atof( col[i+1].c_str() );

      if( m_confidence_override > 0.0 )
      {
        spec_conf = m_confidence_override;
      }

      dot->set_score( spec_id, spec_conf );
    }

    if( COL_TOT < col.size() )
    {
      dob = std::make_shared< kwiver::vital::detected_object>( bbox, conf, dot );
    }
    else
    {
      dob = std::make_shared< kwiver::vital::detected_object>( bbox, conf );
    }

    try
    {
      frame_time = convert_to_timestamp( str_id );
    }
    catch( ... )
    {
      frame_time = frame_id;
    }

    if( found_attribute )
    {
      add_attributes_to_detection( *dob, col );
    }

    // Create new object track state
    kwiver::vital::track_state_sptr ots =
      std::make_shared< kwiver::vital::object_track_state >(
        frame_id, frame_time, dob );

    // Assign object track state to track
    kwiver::vital::track_sptr trk;

    if( m_all_tracks.count( trk_id ) == 0 )
    {
      trk = kwiver::vital::track::create();
      trk->set_id( trk_id );
      m_all_tracks[ trk_id ] = trk;
    }
    else
    {
      trk = m_all_tracks[ trk_id ];
    }

    trk->append( ots );

    // Add track to indexes
    if( !m_batch_load )
    {
      m_tracks_by_frame_id[ frame_id ].push_back( trk );
      m_last_idx = std::max( m_last_idx, frame_id );
    }
  }
}

} // end namespace
