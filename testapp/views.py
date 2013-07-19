from resourceful.views import ResourceView

from testapp.models import Widget


class WidgetView(ResourceView):
    model_class = Widget
