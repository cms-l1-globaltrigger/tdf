# Test and Development Framework (TDF)

Software for communication with AMC boards on MTCA crates.

## Installation of TDF on test and production crates

* Go to TDF repo web side
- select branch for installation
- click on "CODE" button and on "Download ZIP"

* Go to local download directory
$ scp <path zip file> <user>@lxplus.cern.ch:.

* Login on lxplus
$ scp <zip file> <user>@cmsusr:.

* login test or production crate
$ cp ../<user>/<zip file> .
$ unzip <zip file>
$ rm -rf software/tdf
$ mkdir software/tdf
$ cp -r <dir unzipped file>/* software/tdf/.
