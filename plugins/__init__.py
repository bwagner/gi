import importlib
import pkgutil
from pathlib import Path


def init() -> None:
    """
    This function imports all submodules of this package
    """

    def iter_namespace():
        for triple in pkgutil.iter_modules(
            [f"{Path(__file__).parent}"], f"{__name__}."
        ):
            yield triple[1]

    for name in iter_namespace():
        importlib.import_module(name)
