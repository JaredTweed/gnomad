#!/bin/bash

# Change the directory where the script is executed from
cd "$(dirname "$0")/.." || exit

if ! [[ -f "Makefile" ]]; then
  echo "Error: no Makefile"
  exit 1
fi

CURRENT_DIR=$(pwd)
PKGVERSION=$(git describe --tags `git rev-list --tags --max-count=1`)

# Clean old workspace
rm -rf ~/rpmbuild

# Setup the build workspace
rpmdev-setuptree

# Retrieve and prepare the sources
wget https://codeberg.org/tblock/tblock/archive/$PKGVERSION.tar.gz -O ~/rpmbuild/SOURCES/$PKGVERSION.tar.gz
tar -xvf ~/rpmbuild/SOURCES/$PKGVERSION.tar.gz -C ~/rpmbuild/SOURCES/
mv ~/rpmbuild/SOURCES/tblock ~/rpmbuild/SOURCES/tblock-$PKGVERSION
rm -f ~/rpmbuild/SOURCES/$PKGVERSION.tar.gz
cd ~/rpmbuild/SOURCES
tar -czf ~/rpmbuild/SOURCES/$PKGVERSION.tar.gz tblock-$PKGVERSION
cd $CURRENT_DIR
rm -rf ~/rpmbuild/SOURCES/tblock-$PKGVERSION

# Build the source package
rpmbuild -bs tblock.spec

