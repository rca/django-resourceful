import json

from django.core import serializers
from django.db.models.query import QuerySet

class DjangoEncoder(object):
    def __init__(self, fields=None):
        self.fields = fields

    def __call__(self, *args, **kwargs):
        kwargs['_fields'] = self.fields

        return DjangoJSONEncoder(*args, **kwargs)


class DjangoJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        self.fields = kwargs.pop('_fields', None)
        super(DjangoJSONEncoder, self).__init__(*args, **kwargs)

    def default(self, obj):
        # Django serializer returns a JSON string, but we need to return a
        # serializable object, so load up the serialized string as soon as
        # it's returned.
        if isinstance(obj, QuerySet):
            return json.loads(serializers.serialize('json', obj, fields=self.fields))
        elif hasattr(obj, '_meta'):
            # in this case, return just the first element since we had to
            # throw the object into an iterable to serialize it.
            return json.loads(serializers.serialize('json', [obj], fields=self.fields))[0]

        return super(DjangoJSONEncoder, self).default(obj)
