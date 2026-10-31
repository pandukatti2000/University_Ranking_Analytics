import msgpack

class MsgpackEncodeError(Exception):
    pass

class MsgpackDecodeError(Exception):
    pass

def packb(data, default=None, option=0):
    try:
        return msgpack.packb(data, default=default, use_bin_type=True)
    except Exception as e:
        raise MsgpackEncodeError(str(e)) from e

def unpackb(data, ext_hook=None, option=0):
    try:
        return msgpack.unpackb(data, ext_hook=ext_hook, raw=False)
    except Exception as e:
        raise MsgpackDecodeError(str(e)) from e

Ext = msgpack.ExtType

OPT_NON_STR_KEYS = 1
OPT_PASSTHROUGH_DATACLASS = 2
OPT_PASSTHROUGH_DATETIME = 4
OPT_PASSTHROUGH_ENUM = 8
OPT_PASSTHROUGH_UUID = 16
OPT_REPLACE_SURROGATES = 32
