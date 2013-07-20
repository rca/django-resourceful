from resourceful.views import ResourceView

from testapp.models import Widget, Drawing


class DrawingView(ResourceView):
    model_class = Drawing


class WidgetView(ResourceView):
    model_class = Widget
    query_map = {
        'drawing': 'drawing__name',
    }
