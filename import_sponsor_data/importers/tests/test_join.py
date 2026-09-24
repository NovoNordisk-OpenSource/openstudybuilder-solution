from ..utils.path_join import path_join


def test_joining():
    assert path_join("a", "b", "c") == "a/b/c"
    assert path_join("a/", "b", "/c") == "a/b/c"
    assert path_join("a", "b/", "/c/") == "a/b/c/"
    assert path_join("http://localhost:1234", "b/", "/c") == "http://localhost:1234/b/c"
    assert path_join("a", "b-", "-c", separator="-") == "a-b-c"
    assert path_join() == ""
    assert path_join("a") == "a"
