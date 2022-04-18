from textgame.things import StorageManager, Store
from textgame.things import Container, StorageManager, Store
from textgame.exceptions import StoreLimitExceededError
from textgame.loader import Factory
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

    def test_limit(self, managed_stores: Tuple[StorageManager, Dict[str, Store]]):
        manager, stores = managed_stores
        things = manager.storage
        stores["store_0"].limit = 2
        stores["store_0"].add(things["thing_0"])
        stores["store_0"].add(things["thing_1"])
        with pytest.raises(StoreLimitExceededError):
            stores["store_0"].add(things["thing_2"])
        # adding the same thing again should not be a problem?
        stores["store_0"].add(things["thing_1"])


@pytest.fixture
def container() -> Container:
    container_specs = {
        "id": "basket",
        "name": "wooden basket",
        "description": "a wooden basket lies around.",
        "initlocation": "-",
        "type": "container",
        "limit": 1,
    }
    return Factory.create(container_specs)


class TestContainers:
    def test_containerfactory(self, container: Container):
        assert isinstance(container, Container)

    def test_container(self, container: Container, things: Dict[str, MagicMock]):
        things["basket"] = container  # make it nested
        manager = StorageManager(things)
        manager.add_store(container._contains)
        container.insert(things["thing_0"])
        assert "thing_0" in container
        with pytest.raises(StoreLimitExceededError):
            container.insert(things["thing_1"])

        inside = container.pop("thing_0")
        assert inside == things["thing_0"]
        assert container.get_contents() == {}
