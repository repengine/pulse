from collections import defaultdict
from typing import Callable, Dict, List, Any


class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish(self, event_type: str, data: Any = None) -> None:
        for handler in self._subscribers[event_type]:
            handler(data)


# Global event bus instance
event_bus = EventBus()
