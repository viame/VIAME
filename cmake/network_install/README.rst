VIAME Network Installer Creation
================================


Step 1: Generate VIAME Installer
--------------------------------

Use the ``VIAME_CREATE_PACKAGE`` option in CMake to direct CPack to create an
MSI for the VIAME code.  On Windows, this will entail the building of the
``PACKAGE`` target in Visual Studio.

Copy the resultant ``.msi`` file to the directory which contains the
``VIAME_Network.wxs`` file.


Step 2: Generate Supplemental Installers
-----------------------------------------

The supplemental installers are generated via the Python script called
``generate_viame_installers.py``.  This will use multiple processes to
generate an installer for each archive object in a list that is user-specified.

Prior to running the script
+++++++++++++++++++++++++++

Fill in user-specific data:
  * Ensure that the list which describes the archive objects, called
    ``data_name_dict``, is up to date.
  * Ensure that the Girder connection information is correct.  This includes:
    * Username
    * Password
    * API root url
    * Girder parent object Id

All of these objects can be found from line 45 to line 70.

Executing the Python script:
++++++++++++++++++++++++++++

Execute the ``generate_viame_installers.py`` file.  This long running process
will create a set of temporary directories and execute a small CMake process to
generate the installer for each piece of data.  It will then upload the MSI file
to the Girder instance and copy it to the directory where the
``generate_viame_installers.py`` file exists.  This file uses the
multiprocessing library to spawn multiple processes to generate installers in
parallel.  The default number of processes is 4.

The ``generate_viame_installers.py`` has two optional arguments.

``--remake_all`` will create a new installer, whether the target file exists in
the remote folder or not.

``-j`` will allow the user to set a different number of processes to be used.

This script also creates the file needed for the ``Chain`` capbility of the
WiX Toolset based upon the amount of data set.

Step 3: Generate Network Installer
-----------------------------------

3.1 Selectable Options
++++++++++++++++++++++

The VIAME Network system contains a ``VIAME_options.xml`` file.  This file is
used to alter the windows shown when the end user starts the installer.
Specifically, we add ``<Checkbox>`` objects to the ``Options`` page to inform
the installer which other installers to acquire.

If necessary, update the available checkboxes to contain the same options as
those that are found in the ``VIAME_Chain_File.wxs``.  That is, each Checkbox
``name`` should match one found in an ``InstallCondition`` in the ``.wxs``
file.


3.2 Creation of EXE
++++++++++++++++++++

The generation of the network installer is performed in two steps.  First, a
file is passed to the ``candle.exe`` program of the WiX toolset.

.. code-block: sh

  $ candle.exe -ext WixBalExtension VIAME_Network.wxs

The output of that command will have the same name as the input file, but with
a different extension: ``.wixobj``.  This new file is then passed to the
``light.exe`` program.

.. code-block: sh

  $ light.exe -ext WixBalExtension VIAME_Network.wixobj
