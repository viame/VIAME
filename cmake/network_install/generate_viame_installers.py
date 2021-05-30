from argparse import ArgumentParser
import girder_client
import glob
import multiprocessing
import os
import shutil
import signal
import sys
from subprocess import run
from tempfile import TemporaryDirectory
import urllib

run_dir = os.path.dirname(__file__)

cmake_template = """
project({data_name}Data NONE)

if(NOT EXISTS ${{CMAKE_BINARY_DIR}}/{data_name}.zip)
  file(DOWNLOAD https://data.kitware.com/api/v1/item/{data_sha}/download
    ${{CMAKE_BINARY_DIR}}/{data_name}.zip
    SHOW_PROGRESS)
endif()

install(FILES ${{CMAKE_BINARY_DIR}}/{data_name}.zip
  DESTINATION data)

set(CPACK_BINARY_WIX ON CACHE BOOL "Use WIX" FORCE)
set(CPACK_BINARY_NSIS OFF CACHE BOOL "No NSIS" FORCE)

set( CPACK_PACKAGE_VERSION_MAJOR       "{data_version_major}" )
set( CPACK_PACKAGE_VERSION_MINOR       "{data_version_minor}" )
set( CPACK_PACKAGE_VERSION_PATCH       "" )
include(CPack)"""

pkg_template = """<MsiPackage Id="{data_name}Data"
            Name="{file_name}"
            Compressed="no"
            DisplayInternalUI="yes"
            DownloadUrl="{girder_url}/item/{file_id}/download"
            DisplayName="Downloading {file_name}"
            InstallCondition="{data_name}ModelsCheckbox=1">
</MsiPackage>
"""

# !!!!! Before Running:
# Ensure the information below is up to date
gider_parent_folder_id = ""
girder_id = ""
girder_password = ""
girder_url = "https://viame.kitware.com/api/v1"


# Dictionary of descriptive string to
# ITEM Id of the archive file. The ITEM id should
# be reachable on the https://data.kitware.com Girder instance.

data_name_dict = {
  # Models/Data
  "SeaLion1_1": "5f6639dd50a41e3d199a4153",
  "SeaLion1_2": "5fcdb5f150a41e3d198fa856",
  "MOUSS": "5cdec8ac8d777f072bb4457f",
  "MOUSSAlt": "5ce5af728d777f072bd5836d",
  "SEFSC1_1": "5fb69a7450a41e3d1960c6a5",
  "SEFSC1_2": "5fcdb5f150a41e3d198fa856",
  "ArcticSeals": "5e30b8ffaf2e2eed3545bff6",
  "HabCam": "5f6bb7e850a41e3d19a63047",

  # GUI options
  "CPU_GUI_x64":"5fb9ff7350a41e3d196659df",
  "GPU_GUI_x64":"5fbea91550a41e3d19705409"
}
  # End pre-set information
pool_options={}
upload_folder=""
gc = girder_client.GirderClient(apiUrl=girder_url)
def init_folder(options):
  """ A simple function used to initialize each process.
  It signs into the girder instance and collects the upload
  folder.  """
  # Needed to gracefully exit.
  signal.signal(signal.SIGINT, signal.SIG_IGN)

  global gc
  gc.authenticate(girder_id, girder_password)
  new_folder = gc.createFolder(gider_parent_folder_id,
                              "Supplemental Installers",
                              parentType='collection',
                              reuseExisting=True)
  global upload_folder
  upload_folder = new_folder["_id"]
  global data_version_major
  data_version_major = 1
  global data_version_minor
  data_version_minor = 0
  global pool_options
  pool_options=options


def installer_process(data_tuple):
    """ A multiprocess function used to parallelize the generation of each installer
    data tuple contains 3 objects
    (data_name, data_sha, files_list)

    data_name is the key of data_name_dict, data_sha is the value the key points to.
    files_list is a dictionary of a multiprocess manager.  This is used to capture
    the information about the uploaded files and pass it back to the main process.
    """
    # First, check to see if it exists already
    target_name = "{}Data-{}.{}-win32.msi".format(data_tuple[0],
                                                 data_version_major,
                                                 data_version_minor)
    existing_obj = gc.get("item", {"folderId": upload_folder, "name": target_name})
    # if not asked to remake it, skip the
    if pool_options["remake_all"] or not existing_obj:

      with TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "CMakeLists.txt"), "w") as cmake_file:
          text = cmake_template.format(data_name=data_tuple[0],
                                      data_sha=data_tuple[1],
                                      data_version_major=data_version_major,
                                      data_version_minor=data_version_minor)
          cmake_file.write(text)
        run(["cmake", "."], cwd=tmpdir)
        run(["cmake", "--build", ".", "--target", "PACKAGE"], cwd=tmpdir)
        installer_file = glob.glob(os.path.join(tmpdir, "*.msi"))[0] # Should only ever be one
        installer_dir, installer_name = os.path.split(installer_file)
        installer_size = os.path.getsize(installer_file)

        with open(installer_file,"rb") as upload_file:
          data_tuple[2][installer_name] = gc.uploadFile(upload_folder,
                                                    upload_file,
                                                    installer_name,
                                                    installer_size,
                                                    parentType="folder"
                                                    )

        # Additionally, move to __file__'s location for WiX to capture data of
        shutil.move(installer_file, os.path.join(run_dir, installer_name))
    else:
      file_data = existing_obj[0]
      file_data["itemId"] = file_data["_id"]
      data_tuple[2][target_name] = file_data

def main(options):
  gc.authenticate(girder_id, girder_password)

  new_folder = gc.createFolder(gider_parent_folder_id,
                              "Supplemental Installers",
                              parentType='collection',
                              reuseExisting=True)
  process_list = []
  manager = multiprocessing.Manager()
  file_list = manager.dict()
  for item, data in data_name_dict.items():
    process_list.append((item, data, file_list))
  with multiprocessing.Pool(int(options["num_processes"]), init_folder, (options,)) as p:
    p.map(installer_process,process_list)

  with open(os.path.join(run_dir, "VIAME_Chain_File.wxs"), "w") as chain:
    chain.write("<Include>\n")
    for installer_name, installer_data in file_list.items():
      chain.write(pkg_template.format(data_name=installer_name.split("-")[0],
                                      girder_url=girder_url,
                                      file_name=installer_name,
                                      file_id=installer_data["itemId"]))
    chain.write("</Include>")

# Avoid sending HEAD request to GitHub and AWS for VIAME-Dive
#  https://github.com/wixtoolset/issues/issues/6060
# Download now and embed it in the installer.
with open(os.path.join(run_dir,"VIAME-Dive-1.3.0.msi"), "wb") as installer:
  with urllib.request.urlopen("https://github.com/VIAME/VIAME-Web/releases/download/1.3.0/VIAME-Dive-1.3.0.msi") as remote:
    installer.write(remote.read())

if __name__ == "__main__":
    arg = ArgumentParser()
    arg.add_argument(
        "--remake_all",
        action="store_true",
        required=False,
        default=False,
    )
    arg.add_argument(
      "-j", '--num_processes',
      action="store",
      required=False,
      default=4
    )
    options = vars(arg.parse_args(sys.argv[1:]))
    main(options)