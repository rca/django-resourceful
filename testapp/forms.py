from django import forms

from testapp.models import Drawing, Widget


class DrawingForm(forms.ModelForm):
    class Meta:
        model = Drawing


class WidgetForm(forms.ModelForm):
    class Meta:
        model = Widget
