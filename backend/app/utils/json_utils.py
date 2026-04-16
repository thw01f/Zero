"""JSON serialization helpers."""
import json
from datetime import datetime, date
from decimal import Decimal

class DarkLeadEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def dumps(obj, **kwargs) -> str:
    return json.dumps(obj, cls=DarkLeadEncoder, **kwargs)

def loads(s: str) -> any:
    return json.loads(s)
