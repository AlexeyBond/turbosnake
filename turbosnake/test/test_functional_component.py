from turbosnake import Component, ParentComponent, Fragment, functional_component
from turbosnake.test_helpers import TreeTestCase


class FunctionalComponentTest(TreeTestCase):
    def test_create_component_class(self):
        @functional_component()
        def component(**props):
            pass

        self.assertTrue(issubclass(component, Component))

    def test_create_component_class_no_explicit_call(self):
        @functional_component
        def component(**props):
            pass

        self.assertTrue(issubclass(component, Component))

    def test_render_nested(self):
        @functional_component
        def child(**props):
            pass

        @functional_component
        def parent(prop1):
            child(cprop1=prop1)

        with self.tree:
            parent(prop1='bar')

        self.assertTreeMatchesSnapshot()

    def test_create_non_parent_by_default(self):
        @functional_component
        def component(**kwargs):
            pass

        self.assertFalse(issubclass(component, ParentComponent))

    def test_create_parent_when_prop_is_present(self):
        @functional_component
        def component(children):
            pass

        self.assertTrue(issubclass(component, ParentComponent))

    def test_create_non_parent_when_explicitly_forbidden(self):
        @functional_component(children=False)
        def component(children):
            pass

        self.assertFalse(issubclass(component, ParentComponent))

    def test_create_parent_when_explicitly_required(self):
        @functional_component(children=True)
        def component(**kwargs):
            pass

        self.assertTrue(issubclass(component, ParentComponent))

    def test_render_children(self):
        @functional_component
        def parent(children):
            with Fragment():
                children()

        @functional_component
        def child():
            pass

        with self.tree:
            with parent():
                child()

        self.assertTreeMatchesSnapshot()
