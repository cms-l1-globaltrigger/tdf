# Test and Development Framework (TDF) for the level 1 global trigger

Software for communication with AMC boards (MP7 and AMC502) on MTCA crates of Global Trigger.

## Installation of TDF on test and production crates

* Go to TDF repo web side
1. Select branch or tag for installation
2. Click on "CODE" button and on "Download ZIP"

* Go to local download directory
1. Copy zip file to lxplus
  > scp "path zip file" "user"@lxplus.cern.ch:.

* Login on lxplus
1. Copy zip file to cmsusr
  > scp "zip file" "user"@cmsusr:.

* Login test or production crate
1. Copy zip file to "crate" and unzip file 
  > cp ../"user"/"zip file" .
  
  > unzip "zip file"
  
2. Delete all files of tdf directory
  > rm -rf software/tdf/*
  
3. Copy all file from unzipped directory to tdf directory
  > cp -r "dir unzipped file"/* software/tdf/.

4. Delete unzipped directory and zip file
  > rm -rf "dir unzipped file" "zip file"
