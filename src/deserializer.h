/*
 * Copyright 2015 CRS4
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef INC_DESERIALIZER_H
#define INC_DESERIALIZER_H

#include "Python.h"
#include "convert.h"
#include "avro.h"

#define DESERIALIZER_READER_OK 0x1
#define DESERIALIZER_SCHEMA_OK 0x2

typedef struct {
    PyObject_HEAD

    int flags;
    ConvertInfo info;
    char* schema_json;

    avro_schema_t schema;
    avro_value_iface_t *iface;
    avro_reader_t datum_reader;
} AvroDeserializer;

extern PyTypeObject avroDeserializerType;

#endif
