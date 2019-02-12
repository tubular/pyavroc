#!/bin/bash

# Copyright 2015 Byhiras (Europe) Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# NOTE(Christian):

# The following are the commits of Tubular/avro that are *different* from apache/avro,
# the reason we want to do things this way is that it forces us to stay up-to-date with
# the apache/avro master branch, while enjoying the benefits of any fixes there. The way
# it works is we check out the apache/avro master and apply any patches we think are
# necessary on top of that. If upstream merges a PR that fixes it, we simply stop the patch.
# Without this, various MacOS fixes to the build were missing and not working and a wheel
# could not be built at all

#348edbbb     -- applied via: tubularavro/patch/default-values
#86686ffd     -- applied via: tubularavro/patch/default-values
#adff6ea1     -- applied via: tubularavro/patch/default-values
#4a8e9338     -- applied via: tubularavro/patch/default-values
#3edf0909     -- applied via: tubularavro/patch/lz4-compression
#80c4533      -- applied via: fixedavro/avro-1906-file-no-records
#5f4896c      -- fixed upstream via: https://github.com/apache/avro/commit/7f2afa8df4167435f4e92c715d65519d01bda2f8
#473c974      -- applied via: fixedavro/avro-1904-record-no-fields
#3db50a3      -- applied via: tubularavro/patch/value-too-large
#eef7dd7a     -- applied via: fixedavro/avro-1902-c-namespace-null
#4c83611d     -- fixed upstream via: https://github.com/apache/avro/commit/a3957200a86a4582c6622738caacd153f0ad7882
#32065b4f     -- applied via: tubularavro/patch/default-values


do_merge() {
    if ! git merge --no-edit "$@"
    then
        grep -vE '^<<<<<<<|^=======|^>>>>>>>' lang/c/tests/CMakeLists.txt >lang/c/tests/CMakeLists.txt.new
        mv lang/c/tests/CMakeLists.txt.new lang/c/tests/CMakeLists.txt
        git add lang/c/tests/CMakeLists.txt
        git commit --no-edit
    fi
}

set -eux

STATIC=0
[ "${1:-}" = '--static' ] && STATIC=1

cd $(dirname "$0")

MYDIR=$(/bin/pwd)

AVRO=$MYDIR/local_avro

if ! [ -d $AVRO ]
then
    git clone https://github.com/apache/avro $(basename $AVRO)
    cd $AVRO
    git config --local user.name Patch
    git config --local user.email patch@nowhere
    git remote add fixedavro https://github.com/walshb/avro || echo
    git remote update
    do_merge fixedavro/avro-1902-c-namespace-null
    do_merge fixedavro/avro-1904-record-no-fields
    do_merge fixedavro/avro-1906-file-no-records
    git remote add tubularavro https://github.com/tubular/avro || echo
    git remote update
    do_merge tubularavro/patch/value-too-large
    do_merge tubularavro/patch/lz4-compression
    do_merge tubularavro/patch/default-values
fi

# build avro

if ! [ -f $AVRO/dist/lib/libavro.a ] && ! [ -f $AVRO/dist/lib/libavro.so ]
then
    # libavro.a must contain PIC
    mv -n $AVRO/lang/c/src/CMakeLists.txt $AVRO/lang/c/src/orig_CMakeLists
    cp -v $AVRO/lang/c/src/orig_CMakeLists $AVRO/lang/c/src/CMakeLists.txt
    echo 'set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${CMAKE_SHARED_LIBRARY_C_FLAGS}")' >>$AVRO/lang/c/src/CMakeLists.txt
    # workaround bug, see: https://github.com/apache/avro/pull/225
    sed -e 's|{JANSSON_INCLUDE_DIR}|{JANSSON_INCLUDE_DIRS}|' $AVRO/lang/c/CMakeLists.txt >$AVRO/lang/c/CMakeLists.txt.new
    mv $AVRO/lang/c/CMakeLists.txt.new $AVRO/lang/c/CMakeLists.txt

    mkdir -p $AVRO/build $AVRO/dist
    cd $AVRO/build
    cmake -DCMAKE_C_FLAGS='-I/usr/local/include/ -I/usr/include/machine' $AVRO/lang/c -DCMAKE_OSX_ARCHITECTURES='x86_64' -DCMAKE_VERBOSE_MAKEFILE=ON -DCMAKE_INSTALL_PREFIX=$AVRO/dist -DCMAKE_BUILD_TYPE=Release -DTHREADSAFE=true
    make
    make test
    # workaround older cmake
    mv $AVRO/build/avro-c.pc $AVRO/build/src/ || true
    make install

    # use static lib
    [ $STATIC -eq 0 ] || rm -f $AVRO/dist/lib/libavro.so*
    [ $STATIC -eq 0 ] || rm -f $AVRO/dist/lib/libavro.dylib*
fi

PYTHON=${VENV_PYTHON:-python}

# build avro python

case $($PYTHON -c 'import sys; print(sys.version_info.major)') in
    3) AVROPY=$AVRO/lang/py3
        ;;
    *) AVROPY=$AVRO/lang/py
       ;;
esac

cd $AVROPY

rm -rf build
$PYTHON setup.py build

# build pyavroc

cd $MYDIR

rm -rf build dist

export PYAVROC_CFLAGS="-I$AVRO/dist/include"
if [ $STATIC -ne 0 ]
then
    mkdir -p pyavroc/avro
    cp -v local_avro/NOTICE.txt pyavroc/avro/
    # a bit cheesy: get libraries from the cmake link.txt file, except libavro
    PYAVROC_LIBS=$(tr ' ' '\n' <$AVRO/build/src/CMakeFiles/avro-shared.dir/link.txt | grep -e '^-l\|dylib$' | grep -v 'libavro')
    export LDFLAGS="-L$AVRO/dist/lib ${PYAVROC_LIBS}"
    [ -d local_jansson ] && LDFLAGS="$LDFLAGS -L$MYDIR/local_jansson/build/lib"
else
    export LDFLAGS="-L$AVRO/dist/lib -Wl,-rpath,$AVRO/dist/lib"
fi

$PYTHON setup.py build

export PYTHONPATH=$(echo $MYDIR/build/lib*):$(echo $AVROPY/build/lib*)

cd tests

$PYTHON -m pytest -sv .

cd $MYDIR
