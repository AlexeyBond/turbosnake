from turbosnake import Component, ParentComponent, fragment, functional_component, ComponentsCollection
from turbosnake.test_helpers import TreeTestCase


class FunctionalComponentTest(TreeTestCase):
    def render(self, component, **props):
        with self.tree:
            component(**props)

        self.tree.run_tasks()

        return self.tree.root

    def test_create_component_class(self):
        @functional_component()
        def component(**props):
            pass

        self.assertTrue(isinstance(self.render(component), Component))

    def test_create_component_class_no_explicit_call(self):
        @functional_component
        def component(**props):
            pass

        self.assertTrue(isinstance(self.render(component), Component))

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

        self.assertFalse(isinstance(self.render(component), ParentComponent))

    def test_create_parent_when_prop_is_present(self):
        @functional_component
        def component(children):
            pass

        self.assertTrue(isinstance(self.render(component, children=ComponentsCollection()), ParentComponent))

    def test_create_non_parent_when_explicitly_forbidden(self):
        @functional_component(children=False)
        def component(children):
            pass

        self.assertFalse(isinstance(self.render(component, children='not a component collection'), ParentComponent))

    def test_create_parent_when_explicitly_required(self):
        @functional_component(children=True)
        def component(**kwargs):
            pass

        self.assertTrue(isinstance(self.render(component), ParentComponent))

    def test_render_children(self):
        @functional_component
        def parent(children):
            with fragment():
                children()

        @functional_component
        def child():
            pass

        with self.tree:
            with parent():
                child()

        self.assertTreeMatchesSnapshot()
