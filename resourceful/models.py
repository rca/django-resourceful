import sys

from django.db import models
from django.contrib.auth.models import User

class ResourceManager(models.Manager):
    def __init__(self):
        self._user_field = None

        super(ResourceManager, self).__init__()

    def all_for_user(self, user):
        return self.filter_for_user(user)

    def filter_for_user(self, user, *args, **kwargs):
        if self.user_field:
            kwargs.update({
                self.user_field: user.id, # use id because this is for FK
            })

        return self.filter(*args, **kwargs)

    def get_for_user(self, user, *args, **kwargs):
        return self.filter_for_user(user).get(*args, **kwargs)

    @property
    def user_field(self):
        if self._user_field is not None:
            return self._user_field

        for field in self.model._meta.fields:
            if field.rel and field.rel.to == User:
                self._user_field = field.name

        return self._user_field


class ObjectsWrapper(object):
    suffix = '_for_user'

    def __init__(self, model_objects):
        self.model_objects = model_objects

    def __getattribute__(self, item):
        if item.endswith(super(ObjectsWrapper, self).__getattribute__('suffix')):
            return self.objects_method(item)
        else:
            return super(ObjectsWrapper, self).__getattribute__(item)

    def objects_method(self, method_name):
        """
        Returns a for_user specific variant for the requested method if it exists.

        @param method_name: the name of the method to lookup: all, filter, get
        @return: the objects method found
        """
        objects = self.model_objects
        if hasattr(objects, method_name):
            method = getattr(objects, method_name)
        else:
            method = self.strip_first_arg(getattr(objects, method_name.replace(self.suffix,'')))

        return method

    @classmethod
    def strip_first_arg(cls, method):
        def method_wrapper(*args, **kwargs):
            return method(*args[1:], **kwargs)

        return method_wrapper


class ModelWrapper(object):
    def __init__(self, model):
        self.model = model
        self.objects = ObjectsWrapper(model.objects)

    def __getattribute__(self, item):
        dict = super(ModelWrapper, self).__getattribute__('__dict__')

        if item == 'objects':
            return dict['objects']

        return getattr(dict['model'], item)
