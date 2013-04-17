class JSONMixin(object):
    json_fields = None

    def get_json(self):
        json_data = {}

        fields = self._meta.fields
        if self.json_fields:
            fields = filter(lambda field: field.name in self.json_fields, self._meta.fields)

        for field in fields:
            name = field.name
            value = getattr(self, name)

            if value is not None:
                value = self.transform(field, value)

            json_data[name] = value

        for field in self._meta.many_to_many:
            name = field.name
            value = self.transform(field, getattr(self, name))

            json_data[name] = value

        return json_data

    def transform(self, field, value):
        for name in (field.name, value.__class__.__name__, field.__class__.__name__):
            transform_name = 'transform_{}'.format(name).lower()
            transform = getattr(self, transform_name, None)

            if transform:
                value = transform(value)
                break

        return value

    def transform_datetime(self, value):
        return str(value)

    def transform_foreignkey(self, value):
        name = getattr(value, 'name', None)

        return {'id': value.id, 'name': name}

    # alias 1to1 to fk
    transform_onetoonefield = transform_foreignkey

    def transform_manytomanyfield(self, value):
        return dict([(x.name, self.transform_foreignkey(x)) for x in value.all()])
