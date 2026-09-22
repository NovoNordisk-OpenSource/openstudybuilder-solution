# pylint: disable=invalid-name
# pylint: disable=redefined-builtin

from extensions.common import query


def get_node_count() -> int:
    result = query("""
        MATCH (n)
        RETURN count(n) AS node_count
        """)
    return result[0]["node_count"] if result else 0
