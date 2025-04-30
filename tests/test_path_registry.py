import pytest
from core.path_registry import get_path

def test_get_path_keyerror():
    """Test that get_path raises KeyError for a non-existent key."""
    with pytest.raises(KeyError):
        get_path("NON_EXISTENT_KEY")