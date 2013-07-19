import json

from django.test import TestCase

from testapp.models import Drawing, Widget


class FilteringTestCase(TestCase):
    def get_json(self, *args, **kwargs):
        kwargs['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        response = self.client.get(*args, **kwargs)

        data = json.loads(response.content)

        return data

    def setUp(self):
        self.drawing = Drawing.objects.create(name='model1')

        self.w1 = Widget.objects.create(name='item1', drawing=self.drawing, quantity=10)
        self.w2 = Widget.objects.create(name='item2', drawing=self.drawing, quantity=20)

    def test_attribute_filtering(self):
        data = self.get_json('/widget', {'name': 'item1'})

        self.assertEqual(1, len(data['items']))
        self.assertEqual('item1', data['items'][0]['fields']['name'])

    def test_underscore_param_removal(self):
        data = self.get_json('/widget', {'name': 'item1', '_format': 'json'})

        self.assertEqual(1, len(data['items']))

    def test_fk_filter(self):
        data = self.get_json('/widget', {'drawing': 'model1'})

        self.assertEqual(2, len(data['items']))
