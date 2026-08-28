from ..types import derive_cache_key


def test_derive_cache_key_is_stable_for_same_inputs() -> None:
    assert derive_cache_key("mod", "Cls", 1) == derive_cache_key("mod", "Cls", 1)


def test_derive_cache_key_changes_with_version() -> None:
    assert derive_cache_key("mod", "Cls", 1) != derive_cache_key("mod", "Cls", 2)


def test_derive_cache_key_changes_with_module_or_qualname() -> None:
    base = derive_cache_key("mod", "Cls", 1)
    assert derive_cache_key("other_mod", "Cls", 1) != base
    assert derive_cache_key("mod", "OtherCls", 1) != base
