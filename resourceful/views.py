import json
import os

from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.conf.urls import patterns, url
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import six
from django.utils.importlib import import_module
from django.views.generic import View

from resourceful.encoder import DjangoEncoder
from resourceful.forms import ResourceForm
from resourceful.models import ModelWrapper

class RenderError(Exception):
    """
    Raised when a renderer for the requested format is not found
    """


class RoutingError(Exception):
    """
    Raised when unable to parse request path
    """


class ResourceView(View):
    model_class = None
    serialize_fields = None # When None default fields are serialized

    def __init__(self, **kwargs):
        super(ResourceView, self).__init__(**kwargs)

        self._templates = None

    def dispatch(self, request, *args, **kwargs):
        """
        Performs resource routing

        When a _method parameter is passed along with the request, it's used as
        the request method.  This is an easy way to make a button be a DELETE
        method rather than GET.

        GET	/photos	index	display a list of all photos
        GET	/photos/new	new	return an HTML form for creating a new photo
        POST /photos/new	create	create a new photo
        POST	/photos	create	create a new photo
        GET	/photos/:id	show	display a specific photo
        GET	/photos/:id/edit	edit	return an HTML form for editing a photo
        PUT /photos/:id/edit	edit	return an HTML form for editing a photo
        PUT	/photos/:id	update	update a specific photo
        DELETE	/photos/:id	destroy	delete a specific photo
        """
        request.method = request.REQUEST.get('_method', request.method).upper()

        id = kwargs.get('id') or None
        action = kwargs.get('action') or None

        if action is None:
            if id:
                if request.method == 'GET':
                    action = 'show'
                elif request.method == 'PUT':
                    action = 'update'
                elif request.method == 'DELETE':
                    action = 'destroy'
                else:
                    raise RoutingError(
                        'Unsupported method {0} with id {1}'.format(request.method, id)
                    )
            else: # no action, no id
                if request.method == 'GET':
                    action = 'index'
                elif request.method == 'POST':
                    action = 'create'
                else:
                    raise RoutingError(
                        'Unsupported method: {0}'.format(request.method)
                    )
        else:
            if action == 'new' and request.method == 'POST':
                action = 'create'
            elif action == 'edit' and request.method == 'PUT':
                action = 'update'

        kwargs.update({
            'id': id,
            'action': action,
        })

        self.format = request.REQUEST.get('_format')

        # when a format is not explicitly requested and the XMLHttpRequest
        # header is found, route to <action>_json handler if one is defined.
        requested_with = request.META.get('HTTP_X_REQUESTED_WITH')
        if requested_with == 'XMLHttpRequest' and self.format is None:
            self.format = 'json'

        handler = getattr(self, action, self.http_method_not_allowed)

        self.action = action
        self.request = request

        return handler(request, *args, **kwargs)

    def create(self, *args, **kwargs):
        form = self.get_form(self.request.POST)
        if form.is_valid():
            item = form.save()

            # redirect to the item page
            url = self.request.session.pop('next', None)
            if url is None:
                url = self.url_for('show', kwargs={'id': item.id})

            return HttpResponseRedirect(url)

        ctx = {
            'form': form,
        }

        return self.render(ctx)

    def destroy(self, *args, **kwargs):
        item = self.model_class.objects.get_for_user(
            self.request.user, pk=kwargs['id'])
        item.delete()

        return HttpResponseRedirect(self.url_for('index'))

    def edit(self, *args, **kwargs):
        id = kwargs['id']
        item = self.model_class.objects.get_for_user(
            self.request.user, pk=id)

        ctx = self.get_context({
            'form': self.get_form(instance=item),
            'method': 'PUT',
        })

        return self.render(ctx)

    def index(self, *args, **kwargs):
        filter_kwargs = self._get_request_id_params()

        ctx = self.get_context({
            'items': self.model_class.objects.filter_for_user(self.request.user, **filter_kwargs),
        })

        return self.render(ctx)

    def new(self, *args, **kwargs):
        next = self.request.REQUEST.get('next')
        if next:
            self.request.session['next'] = next

        ctx = {
            'form': self.get_form(),
        }

        return self.render(ctx)

    def show(self, *args, **kwargs):
        id = kwargs['id']

        ctx = self.get_context({
            'item': self.model_class.objects.get_for_user(
                self.request.user, pk=id),
        })

        return self.render(ctx)

    def update(self, *args, **kwargs):
        id = kwargs['id']
        item = self.model_class.objects.get_for_user(
            self.request.user, pk=id)

        form = self.get_form(self.request.POST, instance=item)
        if form.is_valid():
            item = form.save()

            # redirect to the item page
            url = self.request.session.pop('next', None)
            if url is None:
                url_name = '{0}.show'.format(item._meta.module_name)
                url = reverse(url_name, kwargs={'id': item.id})

            return HttpResponseRedirect(url)

        return HttpResponse('update')

    #
    # -- Helper methods
    #

    def get_context(self, extra):
        module_name = self.model_class._meta.module_name

        context = {
            'index_url': '{0}.index'.format(module_name),
            'show_url': '{0}.show'.format(module_name),
            'new_url': '{0}.new'.format(module_name),
            'edit_url': '{0}.edit'.format(module_name),
            'action_url': '{0}.edit'.format(module_name),
        }

        context.update(extra)

        return context

    def _get_request_id_params(self):
        kwargs = {}
        query_params = self.request.REQUEST

        for key in query_params:
            if key.endswith('_id'):
                kwargs[key[:-3]] = query_params[key]

        return kwargs

    def render(self, context):
        if self.format in (None, 'html'):
            return render_to_response(
                self.templates,
                context,
                context_instance=RequestContext(self.request)
            )
        else:
            renderer = getattr(self, 'render_{0}'.format(self.format))
            if not renderer:
                raise RenderError('Unable to render {0}'.format(self.format))

            return renderer(context)

    def render_json(self, context):
        """
        Returns a JSON response for the given context
        """

        return HttpResponse(
            json.dumps(context, cls=DjangoEncoder(fields=self.serialize_fields)),
            content_type='application/json'
        )

    @property
    def form_class(self):
        meta = self.model_class._meta

        forms = import_module('{0}.forms'.format(meta.app_label))
        form_name = '{0}Form'.format(meta.object_name)

        return getattr(forms, form_name)

    def get_form(self, data=None, instance=None):
        # pass any query parameter that comes in with the request ending in
        # '_id' as initial form data.  The key should have '_id' stripped off.
        initial = self._get_request_id_params()

        if issubclass(self.form_class, ResourceForm):
            form = self.form_class(data, instance=instance, initial=initial, view=self)
        else:
            form = self.form_class(data, instance=instance, initial=initial)

        return form

    @property
    def template_name(self):
        meta = self.model_class._meta
        template = os.path.join(meta.app_label, meta.module_name, '{0}.html'.format(self.action))

        return template

    @property
    def templates(self):
        if self._templates is not None:
            return self._templates

        self._templates = [
            self.template_name,
            'resourceful/{0}.html'.format(self.action),
        ]

        return self._templates

    def url_for(self, action, args=None, kwargs=None):
        url_name = '{0}.{1}'.format(self.model_class._meta.module_name, action)
        return reverse(url_name, args=args, kwargs=kwargs)

    @classmethod
    def patterns_for(cls, model_class, url_prefix=None, **kwargs):
        if isinstance(model_class, six.string_types):
            app_label, model_name = model_class.split('.', 1)
            model_class = get_model(app_label, model_name)

        url_prefix = url_prefix or model_class._meta.object_name.lower()

        model_wrapper = ModelWrapper(model_class)
        view = cls.as_view(model_class=model_wrapper, **kwargs)

        urlpatterns = patterns('',
            url(r'{0}$'.format(url_prefix), view, name='{0}.index'.format(url_prefix)),
            url(r'{0}/new$'.format(url_prefix), view, kwargs={'action': 'new'}, name='{0}.new'.format(url_prefix)),
            url(r'{0}/(?P<id>[^/]+)$'.format(url_prefix), view, name='{0}.show'.format(url_prefix)),
            url(r'{0}/(?P<id>[^/]+)/edit$'.format(url_prefix), view, kwargs={'action': 'edit'}, name='{0}.edit'.format(url_prefix)),
            url(r'{0}/(?P<id>[^/]+)/(?P<action>[^/]*)$'.format(url_prefix), view, name='{0}.action'.format(url_prefix)),
        )

        return urlpatterns
