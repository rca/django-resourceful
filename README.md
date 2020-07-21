django-resourceful
==================

NOTE: this is proof-of-concept code and is no longer maintained.

Rails-like resourceful routing for Django.

This app aims to provide an easy-to-use routing mechanism that calls view
methods specific to the type of request being made, loosely following
the [resource convention found in Ruby on Rails](http://guides.rubyonrails.org/routing.html).

Below is an example of the routes supported out of the box, for a Photo model:

<table>
    <tr>
        <th>Method</th>
        <th>URL</th>
        <th>{% url %}</th>
        <th>Template var name</th>
        <th>View</th>
        <th>Description</th>
    </tr>
    <tr>
        <td>GET</td>
        <td>/photo</td>
        <td>'photo.index'</td>
        <td>index_url</td>
        <td>index</td>
        <td>display a list of all photos</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/photo/new</td>
        <td>'photo.new'</td>
        <td>new_url</td>
        <td>new</td>
        <td>return an HTML form for creating a new photo</td>
    </tr>
    <tr>
        <td>POST</td>
        <td>/photo/new</td>
        <td>'photo.new'</td>
        <td>index_url</td>
        <td>create</td>
        <td>create a new photo</td>
    </tr>
    <tr>
        <td>POST</td>
        <td>/photo</td>
        <td>'photo.index'</td>
        <td>index_url</td>
        <td>create</td>
        <td>create a new photo</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/photo/:id</td>
        <td>'photo.show'</td>
        <td>show_url</td>
        <td>show</td>
        <td>display a specific photo</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/photo/:id/edit</td>
        <td>'photo.edit'</td>
        <td>edit_url</td>
        <td>edit</td>
        <td>return an HTML form for editing a photo</td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>/photo/:id/edit</td>
        <td>'photo.edit'</td>
        <td>edit_url</td>
        <td>update</td>
        <td>update a specific photo</td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>/photo/:id</td>
        <td>'photo.show'</td>
        <td>show_url</td>
        <td>update</td>
        <td>update a specific photo</td>
    </tr>
    <tr>
        <td>DELETE</td>
        <td>/photo/:id</td>
        <td>'photo.show'</td>
        <td>show_url</td>
        <td>destroy</td>
        <td>delete a specific photo</td>
    </tr>
</table>


Declaring Resources
-------------------

Getting started with the Resourceful app is easy.  Just add resources to your
URLconf.  Resources are declared by adding URL patterns using the
`ResourceView.patterns_for()` helper.  To add resources for the `Photo` model,
add the following to `urls.py`:

```python
[...]

from resourceful.views import ResourceView
from portfolio.models import Photo

urlpatterns = ResourceView.patterns_for(Photo)
```

Additional resources can be added by appending `urlpatterns`:

```python
[...]

from resourceful.views import ResourceView
from blog.models import Entry

urlpatterns += ResourceView.patterns_for(Entry)
```


Template Selection
------------------

Template paths are selected automatically based on the name of the app a model
is in, the name of the model, and the name of the resource requested.  For
example, a `GET` request for a particular `Photo` model item in the `portfolio`
app at the URL `/photo/10` would result in the `show()` method to be called and
rendered using the `portfolio/photo/show.html` template.

If that template does not exist, a basic default template at
`resourceful/show.html` is used instead.


Choosing an output format ... Free API!
---------------------------------------

The routing mechanism also detects the format being requested.  HTML is,
obviously, the default.  When a request is made using AJAX, the format is
automatically changed to JSON based on the `X-Requested-With` HTTP header.

The format can also be requested explicitly by making the request with the
`_format` query parameter set.  Currently only `html` and `json` are supported.

With no additional code, your application can serve JSON data back to the client.


Specifying a request method
---------------------------

Similar to selecting a format, specifying the request method is done by setting
the `_method` query parameter.  For example, the following URL will delete the
photo with ID 10:

```
/photo/10?_method=delete
```


User-based Filtering
--------------------

Queries can be filtered based on the logged in user by setting the model
manager to `ResourceManager`.  Simply set it to be the manager for your
model.  In your models.py:

```python
from django.db import models

from resourceful.models import ResourceManager

class Photo(models.Model):
    [...]

    objects = ResourceManager()
```


Customizing Behavior
--------------------

Customizing the default behavior can be done by subclassing `ResourceView` and
overriding the desired action method.  For example, to change the behavior of
the `index` action, create your own subclass (in your app's views.py):

```python
from resourceful.views import ResourceView

class MyResourceView(ResourceView):
    def index(request, *args, **kwargs):
        < your custom code >
```

In your `urls.py` use `MyResourceView` instead:

```python
[...]

from blog.models import Entry
from myapp.views import MyResourceView

urlpatterns = MyResourceView.patterns_for(Entry)
```


Action Views
------------

With the Resourceful app, views in your application take on a different
meaning.  Views now represent a specific action taking place within the
application.  As an example, here is a typical view handling a form submission:

```python
from django.shortcuts import render
from django.http import HttpResponseRedirect

def contact(request):
    if request.method == 'POST': # If the form has been submitted...
        form = ContactForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            return HttpResponseRedirect('/thanks/') # Redirect after POST
    else:
        form = ContactForm() # An unbound form

    return render(request, 'contact.html', {
        'form': form,
    })
```

The above view handles presenting a form to the user as well as processing a
posted data.  Higher up, there is no distinction whether the request made was
getting data or submitting data.  Additionally, there is no distinction between
posting new data and updating existing data.  Such distinctions are generally
left up to the user and are usually handled all within a single view.

Resourceful views change that.  The above example becomes:

```python
from django.shortcuts import render
from django.http import HttpResponseRedirect

from resourceful.views import ResourceView


class MyResourceView(ResourceView):
    def new(self, request, *args, **kwargs):
        form = ContactForm()

        return render(request, 'contact.html', {
            'form': form,
        })

    def create(self, request, *args, **kwargs):
        form = ContactForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            return HttpResponseRedirect('/thanks/') # Redirect after POST

        return render(request, 'contact.html', {
            'form': form,
        })
```

Here there is no logic necessary for detecting the request's intent; that has
been determined for you in advance.


Installation
------------

If using PIP, add the following to `requirements.txt`:

```
-e git://github.com/rca/django-resourceful.git#egg=django-resourceful
```

It can also be installed on the command line:

```
pip install -e git://github.com/rca/django-resourceful.git#egg=django-resourceful
```
