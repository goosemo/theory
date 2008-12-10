#!/bin/sh
SELF=$(cd $(dirname $0); pwd -P)/
VERSION=0.1.3

cd "$SELF/.."
tar jcvf theory-${VERSION}.tar.bz2 --exclude-from=theory/tar_exclude --exclude-vcs theory
