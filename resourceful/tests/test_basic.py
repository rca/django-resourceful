import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from testapp.models import Drawing


class BasicTestCase(TestCase):
    def test_get_item_json(self):
        # ensure getting an item works
        drawing = Drawing.objects.create(name='drawing1')
        url = reverse('drawing.show', args=(drawing.id,))

        response = self.client.get(url, data={'_format': 'json'})
        response_json = json.loads(response.content)

        self.assertEqual('testapp.drawing', response_json['item']['model'])
