#!/bin/bash -x
[ $# -lt 1 ] && { echo "Missing dir arg. nothing to zip"; exit; } 
[ -f $1.zip ] && { echo "$1.zip already exists"; exit; }
zip -r $1.zip $*
echo "---"
cp -p $1.zip SEMPTools.zip
ls -l  $1.zip SEMPTools.zip
