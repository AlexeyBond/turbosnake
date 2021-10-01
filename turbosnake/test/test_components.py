from turbosnake import fragment, DynamicComponent, Component, Ref, ComponentNotFoundError
from turbosnake._components import Fragment
from turbosnake.test_helpers import TreeTestCase


class ComponentTest(TreeTestCase):
    def test_nested_fragments(self):
        with self.tree:
            with fragment():
                fragment()
                with fragment():
                    fragment()

        self.assertIsComponentInstance(self.tree.root, fragment)
        self.assertEqual(len(list(self.tree.root.mounted_children())), 0)

        self.tree.run_tasks()

        root_children = list(self.tree.root.mounted_children())
        self.assertEqual(len(root_children), 2)
        self.assertIsComponentInstance(root_children[0], fragment)
        self.assertEqual(len(list(root_children[0].mounted_children())), 0)
        self.assertIsComponentInstance(root_children[1], fragment)
        child1_children = list(root_children[1].mounted_children())
        self.assertEqual(len(child1_children), 1)
        self.assertIsComponentInstance(child1_children[0], fragment)

    def test_nested_fragments_snapshot(self):
        """Both verifies again validity of Tree+fragment behavior AND validity of snapshot testing functionality"""
        with self.tree:
            with fragment():
                fragment()
                with fragment():
                    fragment()

        self.assertTreeMatchesSnapshot()

    def test_re_render_on_state_change(self):
        class TestComponent(DynamicComponent):
            def render(self):
                Component(
                    prop1=self.get_state_or_init('state1', None)
                ).insert()

        with self.tree:
            TestComponent().insert()

        self.tree.run_tasks()

        self.assertEqual(None, self.tree.root.get_state('state1'))
        self.assertEqual(None, list(self.tree.root.mounted_children())[0].props['prop1'])

        self.tree.root.set_state('state1', 'Foo')

        self.tree.run_tasks()

        self.assertEqual('Foo', self.tree.root.get_state('state1'))
        self.assertEqual('Foo', list(self.tree.root.mounted_children())[0].props['prop1'])

    def test_re_render_different_children(self):
        class TestComponent(DynamicComponent):
            def render(self):
                wrap = self.get_state_or_init('wrap_in_fragment', False)

                if wrap:
                    with fragment():
                        Component(wrapped=wrap).insert()
                else:
                    Component(wrapped=wrap).insert()

        with self.tree:
            TestComponent().insert()

        self.tree.run_tasks()

        children1 = list(self.tree.root.mounted_children())
        self.assertEqual(1, len(children1))
        self.assertEqual(Component, children1[0].__class__)
        self.assertEqual(False, children1[0].props['wrapped'])

        self.tree.root.set_state('wrap_in_fragment', True)

        self.tree.run_tasks()

        children2 = list(self.tree.root.mounted_children())
        self.assertEqual(1, len(children2))
        self.assertEqual(Fragment, children2[0].__class__)
        children21 = list(children2[0].mounted_children())
        self.assertEqual(1, len(children21))
        self.assertEqual(Component, children21[0].__class__)
        self.assertEqual(True, children21[0].props['wrapped'])

    def test_set_ref(self):
        ref0 = Ref()
        ref1 = Ref()

        with self.tree:
            with fragment(ref=ref0):
                fragment(ref=ref1)

        self.tree.run_tasks()

        self.assertIs(ref0.current, self.tree.root)
        self.assertIs(ref1.current, list(self.tree.root.mounted_children())[0])

    def test_first_matching_ascendant_failure(self):
        ref = Ref()
        with self.tree:
            fragment(ref=ref)

        self.tree.run_tasks()

        with self.assertRaises(ComponentNotFoundError):
            ref.current.first_matching_ascendant(lambda _: False)

    def test_first_matching_ascendant_success(self):
        ref0 = Ref()
        ref1 = Ref()

        with self.tree:
            with fragment():
                with fragment(ref=ref0, flag=True):
                    with fragment():
                        fragment(ref=ref1)

        self.tree.run_tasks()

        self.assertIs(
            ref1.current.first_matching_ascendant(lambda it: it.props.get('flag', False)),
            ref0.current
        )

    def test_first_matching_descendants(self):
        ref0, ref1, ref2 = Ref(), Ref(), Ref()

        with self.tree:
            with fragment(ref=ref0):
                with fragment():
                    with fragment(ref=ref1, flag=True):
                        fragment(flag=True)
                fragment(ref=ref2, flag=True)

        self.tree.run_tasks()

        res = ref0.current.first_matching_descendants(lambda c: c.props.get('flag', False))

        self.assertEqual(
            list(res),
            [ref1.current, ref2.current]
        )
