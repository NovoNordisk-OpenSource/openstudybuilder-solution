import pytest

from clinical_mdr_api.models.study_selections.table import Table, TableDimension


class Undefined:
    pass


def test_table_dimension():
    table_dimension = TableDimension(lambda: Undefined)
    assert table_dimension.size == 0
    assert not list(table_dimension.keys())
    assert not list(table_dimension)

    # Getitem on non-existent index creates that item, and may extend the length of the series
    assert table_dimension[2] is Undefined  # sets index[2] to Undefined and size to 3
    keys = list(range(table_dimension.size))
    values = [Undefined, Undefined, Undefined]
    assert table_dimension.size == len(table_dimension) == 3
    assert list(table_dimension.keys()) == keys
    assert list(table_dimension) == values

    # Repeat the tests, as getitem may alter the series
    assert table_dimension[2] is Undefined
    assert list(table_dimension) == values
    assert list(table_dimension.keys()) == keys
    assert len(table_dimension) == table_dimension.size == 3

    value = "foo"

    # Deleting the last item will shrink the series
    table_dimension[5] = value
    keys = [0, 1, 2, 3, 4, 5]
    values = [Undefined, Undefined, Undefined, Undefined, Undefined, value]
    assert table_dimension[5] == value
    assert table_dimension.size == len(table_dimension) == 6
    assert list(table_dimension.keys()) == keys
    assert list(table_dimension) == values
    # Repeat the tests, as getitem may alter the series
    assert list(table_dimension.keys()) == keys
    assert table_dimension.size == len(table_dimension) == 6
    assert table_dimension[5] == value

    # Deleting the last item will shrink the series
    del table_dimension[5]
    assert table_dimension.size == 5
    assert len(table_dimension) == table_dimension.size
    assert list(table_dimension) == [Undefined] * 5

    # Modifying an item
    value = "bar"
    table_dimension[2] = value
    assert table_dimension.size == 5
    assert len(table_dimension) == table_dimension.size
    assert list(table_dimension) == [Undefined, Undefined, value, Undefined, Undefined]
    assert set(table_dimension.keys()) == set(range(table_dimension.size))

    # Adding an item
    value2 = "waz"
    table_dimension[5] = value2
    assert table_dimension.size == 6
    assert len(table_dimension) == table_dimension.size
    assert list(table_dimension) == [
        Undefined,
        Undefined,
        value,
        Undefined,
        Undefined,
        value2,
    ]
    assert set(table_dimension.keys()) == set(range(table_dimension.size))

    invalid_key = "hello"

    with pytest.raises(KeyError):
        _ = table_dimension[invalid_key]

    with pytest.raises(KeyError):
        table_dimension[invalid_key] = value


def test_table():
    table = Table.new()

    table.data[1][3] = "two; four"
    assert table.data.size == 2
    assert table.data[1].size == 4

    table.meta[1][3]["class"] = "klass"
    assert table.meta.size == 2
    assert table.meta[1].size == 4

    assert table.num_header_rows == 0
    assert table.num_header_columns == 0
