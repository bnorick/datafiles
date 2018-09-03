# pylint: disable=unused-variable

from typing import Dict, List

import pytest

from datafiles import converters


class MyCustomNonDataclass:
    pass


IntegerList = converters.List.of_converters(converters.Integer)  # type: ignore
StringList = converters.List.of_converters(converters.String)  # type: ignore


def describe_map_type():
    def it_handles_list_annotations(expect):
        converter = converters.map_type(List[str])
        expect(converter.__name__) == 'StringList'
        expect(converter.ELEMENT_CONVERTER) == converters.String

    def it_requires_list_annotations_to_have_a_type(expect):
        with expect.raises(TypeError):
            converters.map_type(List)

    def it_rejects_unknown_types(expect):
        with expect.raises(TypeError):
            converters.map_type(MyCustomNonDataclass)

    def it_rejects_unhandled_type_annotations(expect):
        with expect.raises(TypeError):
            converters.map_type(Dict[str, int])


def describe_converter():
    @pytest.mark.parametrize(
        'converter, preserialization_data, python_value',
        [
            (converters.Boolean, '1', True),
            (converters.Boolean, '0', False),
            (converters.Boolean, 'enabled', True),
            (converters.Boolean, 'disabled', False),
            (converters.Boolean, 'T', True),
            (converters.Boolean, 'F', False),
            (converters.Boolean, 'true', True),
            (converters.Boolean, 'false', False),
            (converters.Boolean, 'Y', True),
            (converters.Boolean, 'N', False),
            (converters.Boolean, 'yes', True),
            (converters.Boolean, 'no', False),
            (converters.Boolean, 'on', True),
            (converters.Boolean, 'off', False),
            (converters.Boolean, 0, False),
            (converters.Boolean, 1, True),
            (converters.Float, 4, 4.0),
            (converters.Integer, 4.2, 4),
            (converters.String, 4.2, '4.2'),
            (converters.String, 42, '42'),
            (converters.String, True, 'True'),
            (converters.String, False, 'False'),
            (IntegerList, [], []),
            (IntegerList, '1, 2.3', [1, 2]),
            (IntegerList, '42', [42]),
            (IntegerList, 42, [42]),
            (IntegerList, None, []),
        ],
    )
    def to_python_value(
        converter, preserialization_data, python_value, expect
    ):
        expect(
            converter.to_python_value(preserialization_data)
        ) == python_value

    def to_python_value_when_invalid(expect):
        with expect.raises(ValueError):
            converters.Integer.to_python_value('a')

    @pytest.mark.parametrize(
        'converter, python_value, preserialization_data',
        [
            (converters.Boolean, None, False),
            (converters.Float, None, 0.0),
            (converters.Integer, None, 0),
            (converters.String, None, ''),
            (StringList, 'ab', ['ab']),
            (StringList, ('b', 1, 'A'), ['b', '1', 'A']),
            (StringList, {'b', 1, 'A'}, ['1', 'A', 'b']),
            (StringList, 42, ['42']),
            (StringList, [123, True, False], ['123', 'True', 'False']),
            (StringList, [], []),
            (StringList, None, []),
        ],
    )
    def to_preserialization_data(
        converter, python_value, preserialization_data, expect
    ):
        expect(
            converter.to_preserialization_data(python_value)
        ) == preserialization_data

    def to_preserialization_data_when_invalid(expect):
        with expect.raises(ValueError):
            converters.Integer.to_preserialization_data('a')