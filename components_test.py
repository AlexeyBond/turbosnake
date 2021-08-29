from components import Fragment
from components_test_helpers import TreeTestCase


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

        self.tree.run_tasks()

        self.assertTreeMatchesSnapshot()
