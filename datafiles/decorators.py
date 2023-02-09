import dataclasses
from functools import partial
from pathlib import Path
from typing import Callable, Dict, Optional, Union

from .config import Meta
from .converters import Converter
from .model import create_model


# def datafile(
#     cls_or_pattern: Union[str, Callable, None] = None,
#     *,
#     attrs: Optional[Dict[str, Converter]] = None,
#     manual: bool = Meta.datafile_manual,
#     defaults: bool = Meta.datafile_defaults,
#     infer: bool = Meta.datafile_infer,
#     **kwargs,
# ):
#     """Synchronize a data class to the specified path.

#     Supports the following decoration styles
#     @datafile
#     class Foo:
#         bar: int

#     @datafile("{self.bar}.toml")
#     class Foo:
#         bar: int
#     """

#     if cls_or_pattern is None:
#         return partial(datafile, pattern=None, attrs=attrs, manual=manual, defaults=defaults, infer=infer, **kwargs)

#     def helper(cls, pattern):
#         if dataclasses.is_dataclass(cls):
#             dataclass = cls
#         else:
#             dataclass = dataclasses.dataclass(cls)

#         return create_model(
#             dataclass,
#             attrs=attrs,
#             pattern=pattern,
#             manual=manual,
#             defaults=defaults,
#             infer=infer,
#         )

#     is_pattern = isinstance(cls_or_pattern, str)
#     if is_pattern:
#         return partial(helper, pattern=cls_or_pattern)
#     else:
#         return helper(cls=cls_or_pattern, pattern=None)


def datafile(
    cls=None,
    *,
    pattern: Optional[str] = None,
    attrs: Optional[Dict[str, Converter]] = None,
    manual: bool = Meta.datafile_manual,
    defaults: bool = Meta.datafile_defaults,
    infer: bool = Meta.datafile_infer,
    **kwargs,
):
    """Synchronize a data class to the specified path."""

    if cls is None:
        return partial(datafile, attrs=attrs, manual=manual, defaults=defaults, infer=infer, **kwargs)

    if dataclasses.is_dataclass(cls):
        dataclass = cls
    else:
        dataclass = dataclasses.dataclass(cls)

    return create_model(
        dataclass,
        attrs=attrs,
        pattern=pattern,
        manual=manual,
        defaults=defaults,
        infer=infer,
    )


def auto(filename: str, **kwargs):
    kwargs["infer"] = True

    path = Path.cwd() / filename
    name = path.stem.strip(".").capitalize()

    def auto_repr(self):
        items = (f"{k}={v!r}" for k, v in self.__dict__.items() if k != "datafile")
        params = ", ".join(items)
        return f"{name}({params})"

    cls = type(name, (), {"__repr__": auto_repr})

    return datafile(str(path), **kwargs)(cls)()
