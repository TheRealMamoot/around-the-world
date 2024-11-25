import json
from datetime import datetime, date


def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    # all to string
    return str(obj)
    # raise TypeError("Type %s not serializable" % type(obj))


def json_dumps(data, *args, **kwargs):
    return json.dumps(data, *args, default=json_serializer, **kwargs)


def green_dict(d):  # type: (dict) -> dict
    return json.loads(json_dumps(d))
