#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 CRS4
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


import sys
import pytest

if sys.version_info < (3,):
    from cStringIO import StringIO
    string_io = StringIO
else:
    from io import BytesIO
    string_io = BytesIO

import pyavroc

import avro.schema
from avro.io import DatumReader, BinaryDecoder


SCHEMA = '''{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "office", "type": "string"},
    {"name": "name", "type": "string"},
    {"name": "favorite_number",  "type": ["int", "null"]},
    {"name": "data", "type": "bytes"},
    {"name": "data2", "type": ["null", "bytes"], "default": null}
  ]
}'''


class Deserializer(object):

    def __init__(self, schema_str):
        schema = avro.schema.parse(schema_str)
        self.reader = DatumReader(schema)

    def deserialize(self, rec_bytes):
        return self.reader.read(BinaryDecoder(string_io(rec_bytes)))


def test_exc():
    with pytest.raises(TypeError):
        pyavroc.AvroSerializer(1)
    with pytest.raises(IOError):
        pyavroc.AvroSerializer('NOT_A_VALID_JSON')


def test_serialize_record():
    n_recs = 10
    avtypes = pyavroc.create_types(SCHEMA)
    serializer = pyavroc.AvroSerializer(SCHEMA)
    deserializer = Deserializer(SCHEMA)
    for i in range(n_recs):
        name, office = "name-%d" % i, "office-%d" % i
        avro_obj = avtypes.User(name=name, office=office, data=bytes(b'data bytes'))
        rec_bytes = serializer.serialize(avro_obj)
        deser_rec = deserializer.deserialize(rec_bytes)
        assert set(deser_rec) == set(['name', 'office', 'favorite_number', 'data', 'data2'])
        assert deser_rec['name'] == name
        assert deser_rec['office'] == office
        assert deser_rec['favorite_number'] is None
        assert deser_rec['data'] == bytes(b'data bytes')


def test_serialize_bytearray():
    n_recs = 10
    avtypes = pyavroc.create_types(SCHEMA)
    serializer = pyavroc.AvroSerializer(SCHEMA)
    deserializer = Deserializer(SCHEMA)
    for i in range(n_recs):
        name, office = "name-%d" % i, "office-%d" % i
        avro_obj = avtypes.User(name=name, office=office, data=bytearray(b'data bytes'), data2=bytearray(b'data2 bytes'))
        rec_bytes = serializer.serialize(avro_obj)
        deser_rec = deserializer.deserialize(rec_bytes)
        assert set(deser_rec) == set(['name', 'office', 'favorite_number', 'data', 'data2'])
        assert deser_rec['name'] == name
        assert deser_rec['office'] == office
        assert deser_rec['favorite_number'] is None
        assert deser_rec['data'] == bytes(b'data bytes')
        assert deser_rec['data2'] == bytes(b'data2 bytes')


def test_big():
    avtypes = pyavroc.create_types(SCHEMA)
    serializer = pyavroc.AvroSerializer(SCHEMA)
    long_str = 'X' * (10 * 1024 * 1024)
    avro_obj = avtypes.User(name=long_str, office=long_str, data=b'blah')
    serializer.serialize(avro_obj)


def test_serialize_union():
    schema = '["string", "null"]'
    serializer = pyavroc.AvroSerializer(schema)
    deserializer = Deserializer(schema)
    for datum in "foo", u"foo", None:
        assert deserializer.deserialize(serializer.serialize(datum)) == datum


def test_unicode_map_keys():
    schema = """\
    {"type": "record",
    "name": "foo",
    "fields": [{"name": "bar",
                "type": ["null", {"type": "map", "values": "string"}]}]}
    """
    serializer = pyavroc.AvroSerializer(schema)
    rec_bytes = serializer.serialize({"bar": {"k": "v"}})
    assert serializer.serialize({"bar": {u"k": "v"}}) == rec_bytes


def test_serialize_utf8_string():
    schema = '["string"]'
    serializer = pyavroc.AvroSerializer(schema)
    deserializer = Deserializer(schema)

    if sys.version_info < (3,):
        datum = "barà"
        rec_bytes = serializer.serialize(datum)
        assert deserializer.deserialize(rec_bytes) == unicode(datum, "utf-8")

    datum = u"barà"
    rec_bytes = serializer.serialize(datum)
    assert deserializer.deserialize(rec_bytes) == datum

def test_serialize_reuse_record_type():
    schema = """\
    { "type": "record",
      "name": "foo",
      "namespace": "org.pyavroc",
      "fields": [
        { "name": "c1",
         "type": { "type": "record", "name": "Contig", "fields": [ { "name": "contigName", "type": "string" } ] }
        },
        { "name": "c2",
          "type": [ "null", "Contig" ]
        }
      ]
    }
    """
    ser = pyavroc.AvroSerializer(schema)
    datum = {
            "c1": { "contigName": "contig1" },
            "c2": { "contigName": "contig2" }
            }
    obytes = ser.serialize(datum)
    assert obytes
