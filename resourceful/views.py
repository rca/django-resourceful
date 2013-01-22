import json
import os

from django.core.urlresolvers import reverse
from django.conf.urls import patterns, url
from django.db.models.loading import get_model
from django.forms import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import six
from django.utils.importlib import import_module
from django.views.generic import View

from resourceful.encoder import DjangoEncoder
from resourceful.forms import BaseResourceForm
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
    url_prefix = None
    template_dir = None
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
                    request.PUT = QueryDict(request.body)
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
        if request.is_ajax() and self.format is None:
            self.format = 'json'

        handler = getattr(self, action, self.http_method_not_allowed)

        self.action = action
        self.request = request

        return handler(request, *args, **kwargs)

    def create(self, *args, **kwargs):
        form = self.get_form(self.request.POST)
        if form.is_valid():
            item = form.save()
            return self._create_success(item)

        ctx = {
            'form': form,
        }

        return self._create_error(ctx)

    def _create_success(self, item):
        url = self._get_next_url()
        if url is None:
            url = self.url_for('show', kwargs={'id': item.id})

        return HttpResponseRedirect(url)

    def _create_error(self, ctx):
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
            'item': item,
            'method': 'PUT',
        })

        return self.render(ctx)

    def index(self, *args, **kwargs):
        filter_kwargs = self._get_request_id_params()

        items = self._get_items(**filter_kwargs)

        ctx = self.get_context({
            'items': items,
        })

        return self.render(ctx)

    def _get_items(self, **kwargs):
        return self.model_class.objects.filter_for_user(self.request.user, **kwargs)

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
        item = self.get_item(kwargs['id'])
        form = self.get_form(self.request.PUT, instance=item)

        ctx = {
            'form': form,
            'item': item,
        }

        try:
            self._update_handle_form(form)
            return self._update_success(item)
        except Exception, exc:
            ctx['error'] = exc

        return self._update_error(ctx)

    def get_item(self, id):
        return self.model_class.objects.get_for_user(self.request.user, pk=id)

    def _update_handle_form(self, form):
        if form.is_valid():
            form.save()

    def _update_error(self, ctx):
        return self.render(ctx)

    def _update_success(self, item):
        # redirect to the item page
        url = self._get_next_url()
        if url is None:
            url_name = '{0}.show'.format(item._meta.module_name)
            url = reverse(url_name, kwargs={'id': item.id})

        return HttpResponseRedirect(url)
    #
    # -- Helper methods
    #

    def get_context(self, extra):
        url_prefix = self.url_prefix

        context = {
            'index_url': '{0}.index'.format(url_prefix),
            'show_url': '{0}.show'.format(url_prefix),
            'new_url': '{0}.new'.format(url_prefix),
            'edit_url': '{0}.edit'.format(url_prefix),
            'action_url': '{0}.edit'.format(url_prefix),
        }

        context.update(extra)

        return context

    def _get_next_url(self):
        """
        Returns the next URL.

        This function checks the session for the variable "next" to contain a
        URL for redirection.  It will be popped out of the session and used,
        unless next is also specified in the current request.
        """
        # redirect to the item page or to the specified URL
        # if there is a next URL specified in the session,
        # pop it out of the session ...
        url = self.request.session.pop('next', None)

        # ... but if a URL is specified in this request, it
        # trumps whatever was in the session.  the session
        # should be cleaned out, which is why we pop the
        # session first
        url = self.request.REQUEST.get('next') or url

        return url

    def _get_request_id_params(self):
        """
        pass any query parameter that comes in with the request ending in
        '_id' as initial form data.  The key should have '_id' stripped off.
        """
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
        form_kwargs = {
            'data': data,
            'initial': self._get_request_id_params(),
        }

        if issubclass(self.form_class, BaseModelForm):
            form_kwargs['instance'] = instance

        if issubclass(self.form_class, BaseResourceForm):
            form_kwargs['view'] = self

        form = self.form_class(**form_kwargs)

        return form

    @property
    def template_name(self):
        return os.path.join(self.template_dir, self.url_prefix, '{0}.html'.format(self.action))

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
    def patterns_for(cls, model_class=None, template_dir=None, url_prefix=None, **kwargs):
        if isinstance(model_class, six.string_types):
            t_app_label, t_model_name = model_class.split('.', 1)
            model_class = get_model(t_app_label, t_model_name)

        model_wrapper = None

        if model_class:
            if template_dir:
                raise RoutingError('Do not specify template_dir when giving a model_class')

            url_prefix = url_prefix or model_class._meta.object_name.lower()
            model_wrapper = ModelWrapper(model_class)

            meta = model_class._meta
            template_dir = meta.app_label

        # make sure we have all the vars we need
        if url_prefix is None:
            raise RoutingError(
                'Unable to create patterns without url_prefix or model_class')

        if template_dir is None:
            raise RoutingError(
                'Unable to create patterns without a template_dir or model_class')

        view = cls.as_view(
            model_class=model_wrapper,
            url_prefix=url_prefix,
            template_dir=template_dir,
            **kwargs
        )

        urlpatterns = patterns('',
            url(r'{0}$'.format(url_prefix), view, name='{0}.index'.format(url_prefix)),
            url(r'{0}/new$'.format(url_prefix), view, kwargs={'action': 'new'}, name='{0}.new'.format(url_prefix)),
            url(r'{0}/(?P<id>[^/]+)$'.format(url_prefix), view, name='{0}.show'.format(url_prefix)),
            url(r'{0}/(?P<id>[^/]+)/edit$'.format(url_prefix), view, kwargs={'action': 'edit'}, name='{0}.edit'.format(url_prefix)),
            url(r'{0}/(?P<id>[^/]+)/(?P<action>[^/]*)$'.format(url_prefix), view, name='{0}.action'.format(url_prefix)),
        )

        return urlpatterns
