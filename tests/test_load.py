# pylint: disable=unused-variable

import pytest


def describe_nominal():
    def with_matching_types(write, sample, expect):
        write(
            'tmp/sample.yml',
            """
            bool_: true
            int_: 1
            float_: 2.3
            str_: 'foobar'
            """,
        )

        sample.datafile.load()

        expect(sample.bool_) == True
        expect(sample.int_) == 1
        expect(sample.float_) == 2.3
        expect(sample.str_) == 'foobar'

    def with_convertable_types(write, sample, expect):
        write(
            'tmp/sample.yml',
            """
            bool_: 1
            int_: 2
            float_: 3
            str_: 4
            """,
        )

        sample.datafile.load()

        expect(sample.bool_) == True
        expect(sample.int_) == 2
        expect(sample.float_) == 3.0
        expect(sample.str_) == '4'

    def with_extra_fields(write, sample, expect):
        write(
            'tmp/sample.yml',
            """
            bool_: null
            int_: null
            float_: null
            str_: null

            extra: 5
            """,
        )

        sample.datafile.load()

        expect(hasattr(sample, 'extra')) == False


def describe_alternate_formats():
    def with_json(write, sample_json, expect):
        write(
            'tmp/sample.json',
            """
            {
                "bool_": true,
                "int_": 1,
                "float_": 2.3,
                "str_": "foobar"
            }
            """,
        )

        sample = sample_json
        sample.datafile.load()

        expect(sample.bool_) == True
        expect(sample.int_) == 1
        expect(sample.float_) == 2.3
        expect(sample.str_) == 'foobar'


def describe_default_values():
    @pytest.fixture
    def sample(SampleWithDefaultValues):
        return SampleWithDefaultValues(None, None)

    def with_empty_file(sample, expect):
        with open('tmp/sample.yml', 'w') as f:
            f.write("")

        sample.datafile.load()

        expect(sample.str_with_default) == 'foo'
        expect(sample.str_without_default) == ''

    def with_partial_file(write, sample, expect):
        write(
            'tmp/sample.yml',
            """
            str_without_default: bar
            """,
        )

        sample.datafile.load()

        expect(sample.str_with_default) == 'foo'
        expect(sample.str_without_default) == 'bar'


def describe_nesting():
    def with_defaults(write, sample_nesting, expect):
        write(
            'tmp/sample.yml',
            """
            name: ''
            score: 0.0
            nested:
              name: ''
              score: 0.0
            """,
        )

        sample = sample_nesting
        sample.datafile.load()

        expect(sample.name) == ''
        expect(sample.score) == 0.0
        expect(sample.nested.name) == ''
        expect(sample.nested.score) == 0.0

    def with_convertable_types(write, sample_nesting, expect):
        write(
            'tmp/sample.yml',
            """
            name: 1
            score: '2.3'
            nested:
              name: 4
              score: '5.6'
            """,
        )

        sample = sample_nesting
        sample.datafile.load()

        expect(sample.name) == '1'
        expect(sample.score) == 2.3
        expect(sample.nested.name) == '4'
        expect(sample.nested.score) == 5.6

    def with_missing_keys(write, sample_nesting, expect):
        write(
            'tmp/sample.yml',
            """
            name: foo
            nested:
              name: bar
            """,
        )

        sample = sample_nesting
        sample.datafile.load()

        expect(sample.name) == 'foo'
        expect(sample.score) == 0.0
        expect(sample.nested.name) == 'bar'
        expect(sample.nested.score) == 0.0


def describe_lists():
    def with_conversion(write, SampleWithFloatList, expect):
        write(
            'tmp/sample.yml',
            """
            items: 1, 2.3
            """,
        )

        sample = SampleWithFloatList(None)

        expect(sample.items) == [1.0, 2.3]
