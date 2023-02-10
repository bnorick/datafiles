import dataclasses
from functools import partial
from pathlib import Path
from typing import Callable, Dict, Optional, Union

from .config import Meta
from .converters import Converter
from .model import create_model


def datafile(
    cls_or_pattern: Union[str, Callable, None] = None,
    *,
    attrs: Optional[Dict[str, Converter]] = None,
    manual: bool = Meta.datafile_manual,
    defaults: bool = Meta.datafile_defaults,
    infer: bool = Meta.datafile_infer,
    **kwargs,
):
    """Synchronize a data class to the specified path.

    Supports the following arg/kwarg combinations

        # no args or kwargs => Foo becomes a simple dataclass
        @datafile
        class Foo:
            bar: int

        # no args, unknown kwargs => Foo becomes a dataclass with kwargs passed through
        @datafile(frozen=True)
        class Foo:
            bar: int

        # pattern arg with no kwargs
        @datafile("{self.bar}.toml")
        class Foo:
            bar: int

        # pattern arg with non-default kwargs
        @datafile("{self.bar}.toml", manual=True)
        class Foo:
            bar: int

        # no args with non-default kwargs => Foo has an uninitialized pattern
        @datafile(manual=True)
        class Foo:
            bar: int
    """
    if cls_or_pattern is None:
        if (
            attrs is None
            and manual == Meta.datafile_manual
            and defaults == Meta.datafile_defaults
            and infer == Meta.datafile_infer
        ):
            return dataclasses.dataclass(**kwargs)

    if callable(cls_or_pattern):
        return dataclasses.dataclass(cls_or_pattern)  # type: ignore

    def helper(cls, pattern):
        if dataclasses.is_dataclass(cls):
            dataclass = cls
        else:
            dataclass = dataclasses.dataclass(cls, **kwargs)

        return create_model(
            dataclass,
            attrs=attrs,
            pattern=pattern,
            manual=manual,
            defaults=defaults,
            infer=infer,
        )

    is_pattern = isinstance(cls_or_pattern, str)
    if is_pattern:
        return partial(helper, pattern=cls_or_pattern)
    elif cls_or_pattern is None:
        return partial(helper, pattern=None)
    else:
        return helper(cls=cls_or_pattern, pattern=None)


# def datafile(
#     cls=None,
#     *,
#     pattern: Optional[str] = None,
#     attrs: Optional[Dict[str, Converter]] = None,
#     manual: bool = Meta.datafile_manual,
#     defaults: bool = Meta.datafile_defaults,
#     infer: bool = Meta.datafile_infer,
#     **kwargs,
# ):
#     """Synchronize a data class to the specified path."""

#     if cls is None:
#         return partial(datafile, attrs=attrs, manual=manual, defaults=defaults, infer=infer, **kwargs)

#     if dataclasses.is_dataclass(cls):
#         dataclass = cls
#     else:
#         dataclass = dataclasses.dataclass(cls)

#     return create_model(
#         dataclass,
#         attrs=attrs,
#         pattern=pattern,
#         manual=manual,
#         defaults=defaults,
#         infer=infer,
#     )


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
