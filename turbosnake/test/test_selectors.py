from turbosnake import fragment, functional_component
from turbosnake.test_helpers import TreeTestCase


class SelectorsTest(TreeTestCase):
    def test_select_root(self):
        with self.tree:
            fragment()

        self.tree.run_tasks()
        root = self.tree.root

        self.assertIs(
            self.root_selector().only(),
            root
        )

        self.assertIs(
            self.root_selector().one(),
            root
        )

        self.assertEqual(
            self.root_selector().all(),
            [root]
        )

        self.assertEqual(
            self.root_selector().count(),
            1
        )

    def test_select_children(self):
        with self.tree:
            with fragment(key='root'):
                with fragment(key='selected1'):
                    fragment(key='unselected')
                fragment(key='selected2')

        self.tree.run_tasks()

        expected_selected = list(self.tree.root.mounted_children())

        self.assertEqual(
            self.root_selector().children().all(),
            expected_selected
        )

        self.assertIn(
            self.root_selector().children().one(),
            expected_selected
        )

        self.assertEqual(
            self.root_selector().children().count(),
            2
        )

        with self.assertRaises(Exception):
            self.root_selector().children().only()

    def test_select_none(self):
        with self.tree:
            fragment()

        self.tree.run_tasks()

        self.assertEqual(
            self.root_selector().parents().all(),
            []
        )

        self.assertEqual(
            self.root_selector().parents().count(),
            0
        )

        with self.assertRaises(Exception):
            self.root_selector().parents().one()

        with self.assertRaises(Exception):
            self.root_selector().parents().only()

    def test_select_all_descendants(self):
        with self.tree:
            with fragment(key='root'):
                with fragment(key='selected1'):
                    with fragment(key='alsoSelected'):
                        fragment(key='andThisToo')
                fragment(key='selected2')

        self.tree.run_tasks()

        self.assertEqual(
            self.root_selector().descendants().count(),
            4
        )

        expected_selected_keys = {'selected1', 'selected2', 'alsoSelected', 'andThisToo'}

        self.assertEqual(
            set(map(lambda it: it.key, self.root_selector().descendants())),
            expected_selected_keys
        )

        self.assertIn(
            self.root_selector().descendants().one().key,
            expected_selected_keys
        )

        with self.assertRaises(Exception):
            self.root_selector().descendants().only()

    def test_select_component(self):
        @functional_component
        def tc(children):
            children()

        with self.tree:
            with fragment():
                fragment()
                with fragment():
                    with tc():
                        fragment()
        self.tree.run_tasks()

        self.assertIsComponentInstance(
            selected := self.root_selector().descendants(tc).one(),
            tc
        )

        self.assertIs(
            self.root_selector().descendants(tc).only(),
            selected
        )

        self.assertIs(
            self.root_selector().children(fragment).children(tc).only(),
            selected
        )

        self.assertIs(
            self.root_selector().descendants(fragment).parents(tc).only(),
            selected
        )

    def test_select_by_props(self):
        @functional_component
        def tc(children, x):
            children()

        with self.tree:
            with fragment():
                with tc(x='1'):
                    with fragment(x='2'):
                        with tc(x='2'):
                            ...
                with tc(x='2'):
                    ...
        self.tree.run_tasks()

        self.assertEqual(
            self.root_selector().descendants(props=dict(x='2')).count(),
            3
        )

        self.assertEqual(
            self.root_selector().descendants(tc, props=dict(x='2')).count(),
            2
        )

        self.assertEqual(
            self.root_selector().descendants(props=dict(x='1')).only(),
            # Note: `children()` inserts a fragment, so `tc{x='1'}` is not a direct parent of `fragment{x='2'}`
            self.root_selector().descendants(fragment, props=dict(x='2')).parents().parents().only()
        )
