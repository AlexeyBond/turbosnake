from turbosnake import functional_component, SlottedComponent, fragment, ForbiddenSlotError
from turbosnake.test_helpers import TreeTestCase


class SlotsSupportTest(TreeTestCase):
    def test_should_not_support_slots_by_default(self):
        @functional_component
        def tc():
            ...

        self.assertNotIsInstance(self.render(tc), SlottedComponent)

    def test_should_not_support_slots_when_slots_explicitly_disabled(self):
        @functional_component(slots=False)
        def tc(slot_test=None):
            ...

        self.assertNotIsInstance(self.render(tc), SlottedComponent)

    def test_should_support_slots_when_has_slot_properties(self):
        @functional_component
        def tc(slot_test=None):
            ...

        self.assertIsInstance(self.render(tc), SlottedComponent)

    def test_should_support_slots_when_slots_explicitly_enabled(self):
        @functional_component(slots=True)
        def tc():
            ...

        @functional_component(slots=['test'])
        def tc1():
            ...

        @functional_component(slots={'test': 'slot_test1'})
        def tc2():
            ...

        self.assertIsInstance(self.render(tc), SlottedComponent)
        self.assertIsInstance(self.render(tc1), SlottedComponent)
        self.assertIsInstance(self.render(tc2), SlottedComponent)


@functional_component
def stub(label):
    pass


class SlotsRenderTest(TreeTestCase):
    def test_render_slotted_component(self):
        @functional_component
        def tc(slot_1, slot_2):
            slot_1(key='slot1')
            slot_2(key='slot2')

        with self.tree:
            with tc() as c:
                with c['1']:
                    stub(label='stub-1-1')
                    stub(label='stub-1-2')
                with c['2']:
                    stub(label='stub-2-1')
                    stub(label='stub-2-2')

        self.assertTreeMatchesSnapshot()

    def test_render_slots_with_custom_prop_names(self):
        @functional_component(slots=dict(a='the_slot_named_a', b='another_slot'))
        def tc(the_slot_named_a, another_slot):
            the_slot_named_a(key='slotA')
            another_slot(key='slotB')

        with self.tree:
            with tc() as c:
                with c['a']:
                    stub(label='а')

                with c['b']:
                    stub(label='ь')

        self.assertTreeMatchesSnapshot()


class AllowedSlotsTest(TreeTestCase):
    def test_allow_all_slots_when_slots_set_to_true(self):
        @functional_component(slots=True)
        def tc(slot_x, **kwargs):
            pass

        with self.tree:
            with tc() as c:
                with c['x']:
                    fragment()
                with c['y']:
                    fragment()
                with c['й']:
                    fragment()

        self.tree.run_tasks()

    def test_allow_slots_from_list_when_list_passed(self):
        @functional_component(slots=['x', 'y'])
        def tc(**kwargs):
            pass

        with self.tree:
            with tc() as c:
                with c['x']:
                    fragment()
                    fragment()
                with c['y']:
                    fragment()

        self.tree.run_tasks()

    def test_forbid_slots_not_from_list_when_list_passed(self):
        @functional_component(slots=['x', 'y'])
        def tc(**kwargs):
            pass

        with self.assertRaises(ForbiddenSlotError):
            with self.tree:
                with tc() as c:
                    with c['z']:
                        fragment()

    def test_allow_slots_from_dict(self):
        # noinspection PyPep8Naming
        @functional_component(slots=dict(a='slotA', b='slotB'))
        def tc(slotA, slotB):
            pass

        with self.tree:
            with tc() as c:
                with c['a']:
                    fragment()
                with c['b']:
                    fragment()

        self.tree.run_tasks()

    def test_forbid_slots_not_from_dict(self):
        # noinspection PyPep8Naming
        @functional_component(slots=dict(a='slotA', b='slotB'))
        def tc(slotA, slotB):
            pass

        with self.assertRaises(ForbiddenSlotError):
            with self.tree:
                with tc() as c:
                    with c['z']:
                        fragment()

    def test_forbid_slots_not_from_parameters(self):
        @functional_component
        def tc(slot_a, slot_b):
            pass

        with self.assertRaises(ForbiddenSlotError):
            with self.tree:
                with tc() as c:
                    with c['z']:
                        fragment()
