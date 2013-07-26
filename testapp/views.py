from resourceful.views import ResourceView

from testapp.models import AnotherWidget, Widget, Drawing


class DrawingView(ResourceView):
    model_class = Drawing


class WidgetView(ResourceView):
    model_class = Widget
    query_map = {
        'drawing': 'drawing__name',
    }


class AnotherWidgetView(ResourceView):
    model_class = AnotherWidget
