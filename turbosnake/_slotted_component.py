from abc import ABCMeta, abstractmethod
from typing import Optional, Callable

from ._components import Component, ComponentsCollection, ComponentRenderingContext, ComponentCollectionBuilder
from ._render_context import enter_render_context


class SlotsCollectionBuilder(metaclass=ABCMeta):
    def __init__(self, component: 'SlottedComponent'):
        self.component = component

    def finish(self):
        ...

    def assign_slot(self, prop_name: str, children: ComponentsCollection):
        assert prop_name not in self.component.props.keys(), f'Attempt to reassign slot "{prop_name}"'

        self.component.props[prop_name] = children


class SlotBuilder(metaclass=ABCMeta):
    @abstractmethod
    def on_done(self, children):
        ...

    def __enter__(self):
        assert not hasattr(self, '_SlotBuilder__restore_context')

        self.__restore_context = enter_render_context(ComponentRenderingContext.CONTEXT_ID,
                                                      ComponentCollectionBuilder())

    def __exit__(self, exc_type, exc_val, exc_tb):
        builder = self.__restore_context()
        del self.__restore_context
        self.on_done(builder.build())


class PropSlotBuilder(SlotBuilder):
    def __init__(self, slots_builder: SlotsCollectionBuilder, prop_name: str):
        self.__slots_builder = slots_builder
        self.__prop_name = prop_name

    def on_done(self, children):
        self.__slots_builder.assign_slot(self.__prop_name, children)


class ForbiddenSlotError(Exception):
    def __init__(self, slot, allowed_slots):
        super().__init__(f'Illegal slot name: {slot}. Allowed slot names are: {", ".join(allowed_slots)}')


class NamedSlotsCollectionBuilder(SlotsCollectionBuilder):
    def __init__(self, component: 'SlottedComponent',
                 slot_to_prop_name: Callable,
                 allowed_slots: Optional[set[str]],
                 ):
        super().__init__(component)
        self.__allowed_slots = allowed_slots
        self.__slot_to_prop_name = slot_to_prop_name

    def __getitem__(self, slot):
        if self.__allowed_slots:
            if slot not in self.__allowed_slots:
                raise ForbiddenSlotError(slot=slot, allowed_slots=self.__allowed_slots)

        return PropSlotBuilder(self, self.__slot_to_prop_name(slot))


class SlottedComponent(Component, metaclass=ABCMeta):
    @abstractmethod
    def init_slots_collection(self) -> SlotsCollectionBuilder:
        ...

    def __enter__(self):
        assert not hasattr(self, '_SlottedComponent__slots_collection')

        slots_collection_builder = self.init_slots_collection()
        self.__slots_collection_builder = slots_collection_builder

        return slots_collection_builder

    def __exit__(self, exc_type, exc_val, exc_tb):
        slots_collection_builder = self.__slots_collection_builder

        del self.__slots_collection_builder

        slots_collection_builder.finish()


class PropSlotsComponent(SlottedComponent):
    @staticmethod
    def default_slot_name_to_prop_name(slot: str) -> str:
        return f'slot_{slot}'

    @staticmethod
    def default_prop_name_to_slot_name(prop_name: str) -> str:
        assert prop_name.startswith('slot_')

        return prop_name[5:]

    slot_to_prop_name: Callable = default_slot_name_to_prop_name
    allowed_slots: Optional[set[str]] = None

    def init_slots_collection(self) -> SlotsCollectionBuilder:
        return NamedSlotsCollectionBuilder(
            self,
            slot_to_prop_name=self.slot_to_prop_name,
            allowed_slots=self.allowed_slots
        )
