from django.forms import BaseModelForm
from django.forms.util import ErrorList


class ResourceForm(BaseModelForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None, view=None):

        super(ResourceForm, self).__init__(
            data=data, files=files, auto_id=auto_id, prefix=prefix,
            initial=initial, error_class=error_class, label_suffix=label_suffix,
            empty_permitted=empty_permitted, instance=instance
        )

        self.for_view(view)

    def for_view(self, view):
        """
        Filters any form fields based on the request being made.

        This is a no-op unless implemented in a subclass.

        @param request: The request object
        @return: None
        """
