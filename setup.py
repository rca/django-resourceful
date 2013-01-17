#!/usr/bin/env python

from distutils.core import setup

setup(name='django-resourceful',
      version='0.2',
      description='Resourceful routing for Django',
      author='Roberto Aguilar',
      author_email='roberto.c.aguilar@gmail.com',
      url='http://github.com/rca/django-resourceful',
      packages=['resourceful'],
      package_data={'resourceful': [
          'templates/resourceful/*',
      ]},
     )
