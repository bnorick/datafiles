"""Defines object-relational mapping (ORM) methods to manipulate models."""

from __future__ import annotations

import dataclasses
import inspect
import os
import re
from functools import reduce
from glob import iglob
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Optional

import log
from parse import parse
from ruamel.yaml.error import MarkedYAMLError

from . import hooks, model
from .utils import pattern_uses_self

if TYPE_CHECKING:
    from .model import Model


Trilean = Optional[bool]
Missing = dataclasses._MISSING_TYPE
_NOT_PASSED = object()  # sentinel
_PLACEHOLDER_PATTERN = re.compile(r"\{.*?\}")


class Splats:
    def __getattr__(self, name):
        return "*"


class Manager:
    def __init__(self, cls):
        self.model = cls
        self._pattern = cls.Meta.datafile_pattern
        self._use_self = pattern_uses_self(self._pattern)

    def get(self, *args, **kwargs) -> Model:
        with hooks.disabled():
            instance = self.model.__new__(self.model)

            # We **must** initialize with a value all fields on the uninitialized
            # instance which play a role in loading, e.g., those with placeholders
            # in the pattern. Other init fields of the instance which are not passed
            # as args or kwargs will be set to `dataclasses._MISSING_TYPE` and their
            # values will be loaded over.
            fields = [field for field in dataclasses.fields(self.model) if field.init]
            pattern = self._pattern
            args_iter = iter(args)
            for field in fields:
                placeholder = (
                    "{" + field.name + "}"
                    if not self._use_self
                    else f"{{self.{field.name}}}"
                )

                try:
                    # we always need to consume an arg if it exists,
                    # even if it's not one with a placeholder
                    value = next(args_iter)
                except StopIteration:
                    value = kwargs.get(field.name, _NOT_PASSED)

                if placeholder in pattern:
                    if value is _NOT_PASSED:
                        raise TypeError(
                            f"Manager.get() missing required placeholder field argument: '{field.name}'"
                        )

                if value is _NOT_PASSED:
                    if not isinstance(field.default, Missing):
                        value = field.default
                    elif not isinstance(field.default_factory, Missing):
                        value = field.default_factory()
                    else:
                        value = Missing
                setattr(instance, field.name, value)

            # NOTE: the following doesn't call instance.datafile.load because hooks are disabled currently
            model.Model.__post_init__(instance)

            try:
                instance.datafile.load(_first_load=True)
            except MarkedYAMLError as e:
                log.critical(
                    f"Deleting invalid YAML: {instance.datafile.path} ({e.problem})"
                )
                instance.datafile.path.unlink()
                instance.datafile.load()

            # reconstruct the dataclass so that __init__ gets called
            instance = dataclasses.replace(instance)

            # make sure the mapper knows that it's actually been loaded
            instance.datafile.modified = False

        return instance

    def get_or_none(self, *args, **kwargs) -> Optional[Model]:
        try:
            return self.get(*args, **kwargs)
        except FileNotFoundError:
            log.info("File not found")
            return None

    def get_or_create(self, *args, **kwargs) -> Model:
        try:
            return self.get(*args, **kwargs)
        except FileNotFoundError:
            log.info(f"File not found, creating '{self.model.__name__}' object")
            instance = self.model(*args, **kwargs)
            instance.datafile.save()
            instance.datafile.load()
            return instance

    def all(self, *, _exclude: str = "") -> Iterator[Model]:
        path = Path(self.model.Meta.datafile_pattern).expanduser()
        if path.is_absolute() or self.model.Meta.datafile_pattern[:2] == "./":
            log.debug(f"Detected static pattern: {path}")
        else:
            try:
                root = Path(inspect.getfile(self.model)).parent
            except (TypeError, OSError):
                level = log.DEBUG if "__main__" in str(self.model) else log.WARNING
                log.log(level, f"Unable to determine module for {self.model}")
                root = Path.cwd()
            path = root / self.model.Meta.datafile_pattern
            log.debug(f"Detected dynamic pattern: {path}")

        pattern = str(path.resolve())

        splatted = _PLACEHOLDER_PATTERN.sub("*", pattern).replace(
            f"{os.sep}*{os.sep}", f"{os.sep}**{os.sep}"
        )

        log.info(f"Finding files matching pattern: {splatted}")
        for index, filename in enumerate(iglob(splatted, recursive=True)):

            if Path(filename).is_dir():
                log.debug(f"Skipped matching directory {index + 1}: {filename}")
                continue

            log.debug(f"Found matching path {index + 1}: {filename}")
            result = parse(pattern, filename)
            if result:
                values = list(result.named.values())

                if len(values) > 1 and os.sep in values[-1]:
                    parts = values[-1].rsplit(os.sep, 1)
                    values[-2] = values[-2] + os.sep + parts[0]
                    values[-1] = parts[1]

                if _exclude and values[0].startswith(_exclude):
                    log.debug(f"Skipped loading of excluded value: {values[0]}")
                    continue

                yield self.get(*values)

    def filter(self, *, _exclude: str = "", **query):
        for item in self.all(_exclude=_exclude):
            match = True
            for key, value in query.items():
                # The use of reduce helps to handle nested attribute queries
                if reduce(getattr, [item] + key.split("__")) != value:  # type: ignore
                    match = False
            if match:
                yield item
