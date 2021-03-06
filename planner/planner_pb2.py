# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: planner.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='planner.proto',
  package='',
  syntax='proto3',
  serialized_pb=_b('\n\rplanner.proto\"\x1d\n\tJsonReply\x12\x10\n\x08jsonData\x18\x01 \x01(\t25\n\x0cRoutePlanner\x12%\n\tPlanRoute\x12\n.JsonReply\x1a\n.JsonReply\"\x00\x62\x06proto3')
)




_JSONREPLY = _descriptor.Descriptor(
  name='JsonReply',
  full_name='JsonReply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='jsonData', full_name='JsonReply.jsonData', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=17,
  serialized_end=46,
)

DESCRIPTOR.message_types_by_name['JsonReply'] = _JSONREPLY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

JsonReply = _reflection.GeneratedProtocolMessageType('JsonReply', (_message.Message,), dict(
  DESCRIPTOR = _JSONREPLY,
  __module__ = 'planner_pb2'
  # @@protoc_insertion_point(class_scope:JsonReply)
  ))
_sym_db.RegisterMessage(JsonReply)



_ROUTEPLANNER = _descriptor.ServiceDescriptor(
  name='RoutePlanner',
  full_name='RoutePlanner',
  file=DESCRIPTOR,
  index=0,
  options=None,
  serialized_start=48,
  serialized_end=101,
  methods=[
  _descriptor.MethodDescriptor(
    name='PlanRoute',
    full_name='RoutePlanner.PlanRoute',
    index=0,
    containing_service=None,
    input_type=_JSONREPLY,
    output_type=_JSONREPLY,
    options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_ROUTEPLANNER)

DESCRIPTOR.services_by_name['RoutePlanner'] = _ROUTEPLANNER

# @@protoc_insertion_point(module_scope)
