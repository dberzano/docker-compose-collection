#!/bin/bash -ex

#FILE=TARS/slc7_x86-64/GEANT4/GEANT4-v10.4.2-3.slc7_x86-64.tar.gz
FILE=TARS/slc7_x86-64/GEANT4/GEANT4-v10.4.2-4.slc7_x86-64.tar.gz
#FILE=TARS/slc7_x86-64/GEANT4/GEANT4-v10.4.2-5.slc7_x86-64.tar.gz
#FILE=TARS/slc7_x86-64/vgm/vgm-v4-4-90.slc7_x86-64.tar.gz
#FILE=TARS/slc7_x86-64/ROOT
#FILE=TARS/slc7_x86-64/GEANT4
LOCAL=/tmp/tartest/$(basename $FILE).$$

mkdir -p $(dirname $LOCAL)

rm -fv $LOCAL
if [[ $FILE == *.tar.gz ]]; then
    curl -Lvvvk -f -o $LOCAL https://localhost:6443/$FILE
    md5sum $LOCAL
    ls -l $LOCAL
    rm -fv $LOCAL
else
    curl -Lvvvk https://localhost:6443/$FILE
fi
