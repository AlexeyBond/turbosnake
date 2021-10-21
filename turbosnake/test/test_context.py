from turbosnake import Context, functional_component, use_context, fragment, use_state, ContextNotProvidedError
from turbosnake.test_helpers import TreeTestCase

ctx = Context('test')


@functional_component
def context_user():
    value = use_context(ctx)

    fragment(ctx_value=value)


class ContextTest(TreeTestCase):
    def test_simple_access(self):
        with self.tree:
            with ctx.provider(value='foo'):
                context_user()
        self.tree.run_tasks()

        self.assertEqual(
            'foo',
            self.root_selector().descendants(context_user).children().only().props['ctx_value']
        )

    def test_rerender_on_change(self):
        set_context = None

        @functional_component
        def context_changer(children):
            nonlocal set_context
            context, set_context = use_state('foo')

            with ctx.provider(value=context):
                children()

        with self.tree:
            with context_changer():
                context_user()
        self.tree.run_tasks()

        self.assertEqual(
            'foo',
            self.root_selector().descendants(context_user).children().only().props['ctx_value']
        )

        set_context('bar')
        self.tree.run_tasks()

        self.assertEqual(
            'bar',
            self.root_selector().descendants(context_user).children().only().props['ctx_value']
        )

    def test_error_when_not_provided(self):
        with self.tree:
            context_user()

        with self.assertRaises(ContextNotProvidedError):
            self.tree.run_tasks()

    def test_context_change(self):
        ctx2 = Context('test2')
        set_context = None

        @functional_component
        def varying_context_user():
            nonlocal set_context
            context, set_context = use_state(ctx)
            value = use_context(context)

            fragment(ctx_value=value)

        with self.tree:
            with ctx.provider(value='foo'):
                with ctx2.provider(value='bar'):
                    varying_context_user()
        self.tree.run_tasks()

        self.assertEqual(
            'foo',
            self.root_selector().descendants(varying_context_user).children().only().props['ctx_value']
        )

        set_context(ctx2)
        self.tree.run_tasks()

        self.assertEqual(
            'bar',
            self.root_selector().descendants(varying_context_user).children().only().props['ctx_value']
        )

    def test_safe_unmount_user(self):
        set_context = None
        set_flag = None

        @functional_component
        def context_changer(children):
            nonlocal set_context, set_flag
            context, set_context = use_state('foo')
            flag, set_flag = use_state(True)

            with ctx.provider(value=context):
                if flag:
                    children()

        with self.tree:
            with context_changer():
                context_user()
        self.tree.run_tasks()

        set_flag(False)
        self.tree.run_tasks()

        set_context('bar')
        self.tree.run_tasks()

    def test_safe_unmount_all(self):
        with self.tree:
            with ctx.provider(value='foo'):
                context_user()

        self.tree.run_tasks()

        with self.tree:
            fragment()

        self.tree.run_tasks()
