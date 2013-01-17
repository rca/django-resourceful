from flexmock import flexmock

from django.core.handlers.wsgi import WSGIRequest
from django.test import TestCase

from resourceful.views import ResourceView

class RoutingTestCase(TestCase):
    def test_index(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'GET',
            'wsgi.input': '',
        })

        flexmock(ResourceView).should_receive("index").once()

        view = ResourceView.as_view()
        view(request, resource='foo', id='', action='')

    def test_index_json_with_xmlhttprequest(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'GET',
            'wsgi.input': '',
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
        })

        model = flexmock(objects=flexmock(all=lambda: []))

        flexmock(ResourceView).should_receive("render_json").once()

        view = ResourceView.as_view(model_class=model)
        view(request, resource='foo', id='', action='')

    def test_index_json_with_format(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'GET',
            'wsgi.input': '',
            'QUERY_STRING': '_format=json',
        })

        model = flexmock(objects=flexmock(all=lambda: []))

        flexmock(ResourceView).should_receive("render_json").once()

        view = ResourceView.as_view(model_class=model)
        view(request, resource='foo', id='', action='')

    def test_view_with_different_model(self):
        # make sure that passing in a model class in the as_view() call yields
        # a unique response when the view is called.
        request = WSGIRequest({
            'REQUEST_METHOD': 'GET',
            'wsgi.input': '',
            'QUERY_STRING': '_format=json',
        })

        view1 = ResourceView.as_view(model_class=flexmock(objects=flexmock(get=lambda *args, **kwargs: 'view1')))
        view2 = ResourceView.as_view(model_class=flexmock(objects=flexmock(get=lambda *args, **kwargs: 'view2')))

        response1 = view1(request, resource='foo', id='1', action='')
        response2 = view2(request, resource='foo', id='1', action='')

        self.assertNotEqual(response1, response2)

    def test_new(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'GET',
            'wsgi.input': '',
        })

        model = flexmock(
            _meta=flexmock(app_label='foo', module_name='bar'),
            objects=flexmock(get=lambda *args, **kwargs: flexmock())
        )

        flexmock(ResourceView).should_receive("new").once()

        view = ResourceView.as_view(model_class=model)
        view(request, resource='foo', id='', action='new')

    def test_create(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'POST',
            'wsgi.input': '',
        })

        flexmock(ResourceView).should_receive("create").once()

        view = ResourceView.as_view()
        view(request, resource='foo', id='', action='')

    def test_show(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'GET',
            'wsgi.input': '',
        })

        flexmock(ResourceView).should_receive("show").once()

        view = ResourceView.as_view()
        view(request, resource='foo', id='10', action='')

    def test_edit(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'GET',
            'wsgi.input': '',
        })

        flexmock(ResourceView).should_receive("edit").once()

        view = ResourceView.as_view()
        view(request, resource='foo', id='10', action='edit')

    def test_update(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'PUT',
            'wsgi.input': '',
        })

        flexmock(ResourceView).should_receive("edit").once()

        view = ResourceView.as_view()
        view(request, resource='foo', id='10', action='')

    def test_update(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'PUT',
            'wsgi.input': '',
        })

        flexmock(ResourceView).should_receive("update").once()

        view = ResourceView.as_view()
        view(request, resource='foo', id='10', action='')

    def test_destroy(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'DELETE',
            'wsgi.input': '',
        })

        flexmock(ResourceView).should_receive("destroy").once()

        view = ResourceView.as_view()
        view(request, resource='foo', id='10', action='')
