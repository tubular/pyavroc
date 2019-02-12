pyavroc
=======

[![Build Status](https://travis-ci.org/Byhiras/pyavroc.svg?branch=master)](https://travis-ci.org/Byhiras/pyavroc)

An Avro file reader/writer for Python.

Usage
-----

```python
>>> import pyavroc
>>> with open('myfile.avro') as fp:
>>>     reader = pyavroc.AvroFileReader(fp, types=True)
>>>     for record in reader:
>>>         print record
```

Comparison with original Avro Python API
----------------------------------------

pyavroc is a Python API on top of upstream Avro-C. This means it reads about 40 times faster than Avro's Python implementation. (The exact timings depend on the version of Python used).

Name                                              | Description                         | Relative speed (bigger is better)
--------------------------------------------------|-------------------------------------|----------------------------------
[python-avro](https://github.com/apache/avro.git) | Avro's implementation (pure Python) | 1
[fastavro](https://bitbucket.org/tebeka/fastavro) | python-avro improved, using Cython  | 10
[pyavroc](https://github.com/Byhiras/pyavroc.git) | Python/C API on upstream Avro-C     | 40

Building the module
-------------------

We've changed how to build the module, you now only have to:

```
make dist
make publish JENKINS_HOST= JENKINS_JOB= S3_bucket=
```

This will:
1. clone the official apache avro repo
1. take patches that are branches here: https://github.com/Tubular/avro
1. merge them into the apache avro repo
1. build apache/avro with the patches applied
1. test apache/avro
1. build tubular/pyavro (C-extension)
1. test tubular/pyavro
1. create a wheel out of tubular/pyavro
1. publish the wheel to pypi repo on s3


Writing records
---------------

pyavroc supports writing, both for records created as dictionaries, and for records created as Python objects.

More examples
-------------

More examples are available in the `tests` directory.

License
-------

Copyright 2015 Byhiras (Europe) Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
