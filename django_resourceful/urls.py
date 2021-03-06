from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
from testapp.views import DrawingView, WidgetView, AnotherWidgetView


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'django_resourceful.views.home', name='home'),
    # url(r'^django_resourceful/', include('django_resourceful.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)


urlpatterns += WidgetView.patterns()
urlpatterns += AnotherWidgetView.patterns()
urlpatterns += DrawingView.patterns()
