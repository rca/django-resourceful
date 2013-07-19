import os

from django.test import TestCase
from django.utils.importlib import import_module


def find_test_modules(module_path):
    module_dir = os.path.realpath(os.path.dirname(module_path))
    scope = {}

    for filename in os.listdir(module_dir):
        if not (filename.startswith('test_') and filename.endswith('.py')):
            continue

        project_root = get_project_root()

        module_name = filename.replace('.py', '')
        module_path = '{0}.{1}'.format(
            module_dir.replace(project_root, ''), module_name).replace('/', '.')[1:]

        module = import_module(module_path)

        for name in dir(module):
            item = getattr(module, name)

            try:
                if issubclass(item, TestCase):
                    scope[name] = item
            except TypeError:
                pass

    return scope


def get_project_root():
    """
    Look for the nearest .git directory
    """

    last_dir = None
    curr_dir = os.path.dirname(__file__)

    while last_dir != curr_dir:
        manage_py = os.path.join(curr_dir, 'manage.py')
        if os.path.exists(manage_py):
            return curr_dir

        curr_dir = os.path.dirname(curr_dir)

    raise Exception('project root not found')
