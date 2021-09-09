from turbosnake import Fragment, DynamicComponent, Component
from turbosnake.test_helpers import TreeTestCase


class ComponentTest(TreeTestCase):
    def test_nested_fragments(self):
        with self.tree:
            with Fragment():
                Fragment()
                with Fragment():
                    Fragment()

        self.assertIsInstance(self.tree.root, Fragment)
        self.assertEqual(len(list(self.tree.root.mounted_children())), 0)

        self.tree.run_tasks()

        root_children = list(self.tree.root.mounted_children())
        self.assertEqual(len(root_children), 2)
        self.assertIsInstance(root_children[0], Fragment)
        self.assertEqual(len(list(root_children[0].mounted_children())), 0)
        self.assertIsInstance(root_children[1], Fragment)
        child1_children = list(root_children[1].mounted_children())
        self.assertEqual(len(child1_children), 1)
        self.assertIsInstance(child1_children[0], Fragment)

    def test_nested_fragments_snapshot(self):
        """Both verifies again validity of Tree+Fragment behavior AND validity of snapshot testing functionality"""
        with self.tree:
            with Fragment():
                Fragment()
                with Fragment():
                    Fragment()

        self.assertTreeMatchesSnapshot()

    def test_re_render_on_state_change(self):
        class TestComponent(DynamicComponent):
            def render(self):
                Component(
                    prop1=self.get_state_or_init('state1', None)
                )

        with self.tree:
            TestComponent()

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
                    with Fragment():
                        Component(wrapped=wrap)
                else:
                    Component(wrapped=wrap)
        
        with self.tree:
            TestComponent()
        
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
