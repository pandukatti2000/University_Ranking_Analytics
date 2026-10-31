import json
import uuid
from datetime import datetime, date
from decimal import Decimal

class JSONDecodeError(Exception):
    pass

class JSONEncodeError(Exception):
    pass

OPT_NON_STR_KEYS = 1
OPT_SORT_KEYS = 2
OPT_INDENT_2 = 4
OPT_SERIALIZE_NUMPY = 8
OPT_SERIALIZE_DATACLASS = 16
OPT_SERIALIZE_UUID = 32
OPT_NAIVE_UTC = 64
OPT_STRICT_INTEGER = 128
OPT_PASSTHROUGH_SUBCLASS = 256
OPT_PASSTHROUGH_DATETIME = 512
OPT_APPEND_NEWLINE = 1024
OPT_OMIT_MICROSECONDS = 2048

def _default_serializer(obj):
    if hasattr(obj, "tolist") and callable(obj.tolist):
        return obj.tolist()
    if hasattr(obj, "item") and callable(obj.item):
        return obj.item()
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, "to_plotly_json") and callable(obj.to_plotly_json):
        return obj.to_plotly_json()
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def dumps(obj, default=None, option=0):
    indent = 2 if (option & OPT_INDENT_2) else None
    sort_keys = bool(option & OPT_SORT_KEYS)
    
    def custom_default(o):
        if default is not None:
            try:
                return default(o)
            except Exception:
                pass
        return _default_serializer(o)

    try:
        res = json.dumps(
            obj,
            default=custom_default,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=False
        )
        if option & OPT_APPEND_NEWLINE:
            res += "\n"
        return res.encode("utf-8")
    except Exception as e:
        raise JSONEncodeError(str(e)) from e

def loads(s):
    try:
        if isinstance(s, (bytes, bytearray)):
            s = s.decode("utf-8")
        return json.loads(s)
    except Exception as e:
        raise JSONDecodeError(str(e)) from e
