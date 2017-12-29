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

set -eux

cd $(dirname "$0")

MYDIR=$(/bin/pwd)

PYTHON=${PYTHON:-python3.5}

LIBAVRO=$1

cd $MYDIR

rm -rf build dist

export PYAVROC_CFLAGS="-I/usr/include/avro"
export LDFLAGS="-L/usr/lib/$LIBAVRO -Wl,-rpath,/usr/lib/$LIBAVRO"

$PYTHON setup.py build

cd build/lib*/pyavroc

cd $MYDIR

export PYTHONPATH=$(echo $MYDIR/build/lib*)
cd tests

$PYTHON -m pytest -sv .

cd $MYDIR

$PYTHON setup.py bdist_wheel
