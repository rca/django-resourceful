import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from testapp.models import Drawing


class BasicTestCase(TestCase):
    def setUp(self):
        self.drawing = Drawing.objects.create(name='drawing1')

    def test_get_item_json(self):
        # ensure getting an item works
        url = reverse('drawing.show', args=(self.drawing.id,))

        response = self.client.get(url, data={'_format': 'json'})
        response_json = json.loads(response.content)

        self.assertEqual('testapp.drawing', response_json['item']['model'])

    def test_put_with_action(self):
        url = reverse('drawing.edit', args=(self.drawing.id,))

        response = self.client.post(url, data={'name': 'renamed', '_method': 'put'})

        self.assertEqual(302, response.status_code)
