from textgame.things import StorageManager, Store
from unittest.mock import MagicMock
import pytest
from typing import Dict, List, Tuple


@pytest.fixture
def things() -> Dict[str, MagicMock]:
    fakethings = {}
    for i in range(5):
        thing = MagicMock()
        thing.id = f"thing_{i}"
        fakethings[f"thing_{i}"] = thing
    return fakethings


@pytest.fixture
def stores() -> Dict[str, Store]:
    return {f"store_{i}": Store(f"store_{i}") for i in range(2)}


@pytest.fixture
def managed_stores(things, stores) -> Tuple[StorageManager, Dict[str, Store]]:
    mgr = StorageManager(things)
    for store in stores.values():
        mgr.add_store(store)
    return mgr, stores


class TestStores:

    def test_add(self, managed_stores: Tuple[StorageManager, Dict[str, Store]]):
        manager, stores = managed_stores
        things = manager.storage
        stores["store_0"].add(things["thing_1"])
        assert "thing_1" in stores["store_0"].items()
        assert "thing_1" not in stores["store_1"].items()
        stores["store_0"].add(things["thing_2"])
        assert "thing_2" in stores["store_0"].items() 
        assert "thing_1" in stores["store_0"].items()
        # adding a thing to another store should remove it from the other one
        stores["store_1"].add(things["thing_2"])
        assert "thing_2" in stores["store_1"].items()
        assert "thing_2" not in stores["store_0"].items()

    def test_get(self, managed_stores: Tuple[StorageManager, Dict[str, Store]]):
        manager, stores = managed_stores
        things = manager.storage
        stores["store_0"].add(things["thing_0"])
        assert stores["store_0"].get("thing_0") == things["thing_0"]
