#!/usr/bin/env python

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
import json

import avro.schema
from avro.io import DatumWriter, BinaryEncoder, DatumReader, BinaryDecoder

import pytest

if sys.version_info < (3,):
    from cStringIO import StringIO
    string_io = StringIO
else:
    from io import BytesIO
    string_io = BytesIO

import pyavroc

SCHEMA = '''{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "office", "type": "string"},
    {"name": "name", "type": "string"},
    {"name": "favorite_number",  "type": ["int", "null"]}
  ]
}'''


class Deserializer(object):
    def __init__(self, schema_str):
        if sys.version_info >= (3,):
            schema = avro.schema.Parse(schema_str)
        else:
            schema = avro.schema.parse(schema_str)
        self.reader = DatumReader(schema)

    def deserialize(self, rec_bytes):
        return self.reader.read(BinaryDecoder(string_io(rec_bytes)))


class Serializer(object):

    def __init__(self, schema_str):
        if sys.version_info >= (3,):
            schema = avro.schema.Parse(schema_str)
        else:
            schema = avro.schema.parse(schema_str)
        self.writer = DatumWriter(schema)

    def serialize(self, record):
        f = string_io()
        encoder = BinaryEncoder(f)
        self.writer.write(record, encoder)
        return f.getvalue()


def test_exc():
    with pytest.raises(TypeError):
        pyavroc.AvroDeserializer(1)
    with pytest.raises(IOError):
        pyavroc.AvroDeserializer('NOT_A_VALID_JSON')


def test_deserialize_record():
    n_recs = 10
    serializer = Serializer(SCHEMA)
    deserializer = pyavroc.AvroDeserializer(SCHEMA)
    obj_deserializer = pyavroc.AvroDeserializer(SCHEMA, types=True)
    for i in range(n_recs):
        name, office = "name-%d" % i, "office-%d" % i
        record = {'name': name, 'office': office}
        rec_bytes = serializer.serialize(record)
        deser_rec = deserializer.deserialize(rec_bytes)
        assert set(deser_rec) == set(['name', 'office', 'favorite_number'])
        assert deser_rec['name'] == name
        assert deser_rec['office'] == office
        assert deser_rec['favorite_number'] is None
        deser_rec = obj_deserializer.deserialize(rec_bytes)
        assert deser_rec.name == name
        assert deser_rec.office == office
        assert deser_rec.favorite_number is None


def test_big():
    deserializer = pyavroc.AvroDeserializer(SCHEMA)
    long_str = 'X' * (10 * 1024 * 1024)
    long_rec_bytes = Serializer(SCHEMA).serialize(
        {'name': long_str, 'office': long_str}
    )
    deserializer.deserialize(long_rec_bytes)


def test_enum():
    schema = '''{
    "type": "enum",
    "name": "suits",
    "symbols": ["CLUBS", "DIAMONDS", "HEARTS", "SPADES"]
    }'''
    symbols = json.loads(schema)['symbols']
    serializer = Serializer(schema)
    deserializer = pyavroc.AvroDeserializer(schema)
    for s in symbols:
        assert deserializer.deserialize(serializer.serialize(s)) == s

def test_resolution():
    schema_write = '''{
        "type": "record",
        "name": "User",
        "fields": [
            {"name": "a", "type": "int"},
            {"name": "b", "type": "string"},
            {"name": "c",  "type": ["int", "null"]},
            {"name": "d",  "type": ["float", "null"]},
            {"name": "e",  "type": {
                    "type": "long",
                    "logicalType": "timestamp-millis"
                }
            }
        ]
    }'''

    schema_read = '''{
        "type": "record",
        "name": "User",
        "fields": [
            {"name": "a", "type": "double"},
            {"name": "b", "type": "string"},
            {"name": "c",  "type": ["float", "null"]},
            {"name": "d",  "type": "float"},
            {"name": "e",  "type": {
                    "type": "long",
                    "logicalType": "timestamp-millis"
                }
            },
            {"name": "f", "type": "string", "default": "default f value"}
        ]
    }'''
    serializer = Serializer(schema_write)
    deserializer = pyavroc.AvroDeserializer(schema_read)
    record = {
        'a': 1,
        'b': 'the string value',
        'c': 2,
        'd': 3.0,
        'e': 12345,
    }
    rec_bytes = serializer.serialize(record)
    deser_rec = deserializer.deserialize(rec_bytes, writer_schema=schema_write)
    assert deser_rec['a'] == 1.0
    assert deser_rec['b'] == 'the string value'
    assert deser_rec['c'] == 2.0
    assert deser_rec['d'] == 3.0
    assert deser_rec['e'] == 12345
    assert deser_rec['f'] == 'default f value'


def test_bytes():
    sch1 = '''{
        "type": "record",
        "name": "Test",
        "fields": [
            {"name": "bytes_field", "type": "bytes"}
        ]
    }'''

    sch2 = '''{
        "type": "record",
        "name": "Test",
        "fields": [
            {"name": "bytes_field", "type": "bytes"}
        ]
    }'''

    serializer = pyavroc.AvroSerializer(sch1)
    deserializer = pyavroc.AvroDeserializer(sch2)
    data = {"bytes_field": b'some bytes'}

    ser_python_avro = Serializer(sch1).serialize(data)

    res_pyavroc = deserializer.deserialize(ser_python_avro, writer_schema=sch1)
    res_python_avro = Deserializer(sch2).deserialize(ser_python_avro)
    assert res_pyavroc['bytes_field'] == res_python_avro['bytes_field'] == b'some bytes'
