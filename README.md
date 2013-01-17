django-resourceful
==================

Rails-like resourceful routing for Django.

This app aims to provide an easy-to-use routing mechanism that calls view
methods specific to the type of request being made, loosely following
the [resource convention found in Ruby on Rails](http://guides.rubyonrails.org/routing.html).

Below is an example of the routes supported out of the box, for a Photo model:

<table>
    <tr>
        <th>Request Method</th>
        <th>URL</th>
        <th>View Method</th>
        <th>Description</th>
    </tr>
    <tr>
        <td>GET</td>
        <td>/photo</td>
        <td>index</td>
        <td>display a list of all photos</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/photo/new</td>
        <td>new</td>
        <td>return an HTML form for creating a new photo</td>
    </tr>
    <tr>
        <td>POST</td>
        <td>/photo/new</td>
        <td>create</td>
        <td>create a new photo</td>
    </tr>
    <tr>
        <td>POST</td>
        <td>/photo</td>
        <td>create</td>
        <td>create a new photo</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/photo/:id</td>
        <td>show</td>
        <td>display a specific photo</td>
    </tr>
    <tr>
        <td>GET</td>
        <td>/photo/:id/edit</td>
        <td>edit</td>
        <td>return an HTML form for editing a photo</td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>/photo/:id/edit</td>
        <td>update</td>
        <td>update a specific photo</td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>/photo/:id</td>
        <td>update</td>
        <td>update a specific photo</td>
    </tr>
    <tr>
        <td>DELETE</td>
        <td>/photo/:id</td>
        <td>destroy</td>
        <td>delete a specific photo</td>
    </tr>
</table>


Choosing an output format
-------------------------

The routing mechanism also detects the format being requested.  HTML is,
obviously, the default.  When a request is made using AJAX, the format is
automatically changed to JSON based on the `X-Requested-With` HTTP header.

The format can also be requested explicitly by making the request with the
`_format` query parameter set.  Currently only `html` and `json` are supported.


Template Selection
------------------

Template paths are selected automatically based on the name of the app a model
is in, the name of the model, and the name of the resource requested.  For
example, a `GET` request for a particular `Photo` model item in the `portfolio`
app at the URL `/photo/10` would result in the `show()` method to be called and
rendered using the `portfolio/photo/show.html` template.

If that template does not exist, a basic default template at
`resourceful/show.html` is used instead.


Declaring Resources
-------------------

Resources are declared by adding URL patterns using the
`ResourceView.patterns_for()` helper.  To add resources for the `Photo` model,
add the following to `urls.py`:

```python
[...]

from portfolio.models import Photo

urlpatterns = ResourceView.patterns_for(Photo)
```

Additional resources can be added by appending `urlpatterns`:

```python
[...]

from blog.models import Entry

urlpatterns += ResourceView.patterns_for(Entry)
```


Customizing Behavior
--------------------

Customizing the default behavior can be done by subclassing `ResourceView` and
overriding the desired action method.  For example, to change the behavior of
the `list` action, create your own subclass (in your app's views.py):

```python
from resourceview.views import ResourceView

class MyResourceView(ResourceView):
    def list(request, *args, **kwargs):
        < your custom code >
```

In your `urls.py` use `MyResourceView` instead:

```python
[...]

from blog.models import Entry
from myapp.views import MyResourceView

urlpatterns = MyResourceView.patterns_for(Entry)
```
