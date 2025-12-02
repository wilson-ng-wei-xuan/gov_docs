import importlib
import inspect
import pkgutil
import sys
import types
import typing


def list_sub_modules_path(module: types.ModuleType) -> typing.List[str]:
    """
    Recursively find all submodules in the input module. Return paths of the modules
    """
    path_list = []
    spec_list = []
    for importer, modname, ispkg in pkgutil.walk_packages(module.__path__):
        import_path = f"{module.__name__}.{modname}"
        if ispkg:
            spec = pkgutil._get_spec(importer, modname)
            importlib._bootstrap._load(spec)
            spec_list.append(spec)
        else:
            path_list.append(import_path)
    for spec in spec_list:
        del sys.modules[spec.name]
    return path_list


def list_classes_in_module(module_path: str) -> typing.Dict[str, object]:
    """
    list all classe objects in a module. Return a dictionary with class_name: class_object
    """
    module = importlib.import_module(module_path)
    cls_dict = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            cls_dict[name] = obj
    return cls_dict
