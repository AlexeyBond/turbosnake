from unittest.mock import Mock

from turbosnake import functional_component, use_self, Ref, use_state, Component, use_toggle, fragment, use_previous, \
    use_ref, use_effect
from turbosnake._hooks import HookSequenceError, use_callback_proxy, use_callback, use_memo
from turbosnake.test_helpers import TreeTestCase


class HookErrorsTest(TreeTestCase):
    def test_when_render_more_hooks(self):
        set_state = None

        @functional_component
        def tc():
            nonlocal set_state
            state, set_state = use_state(False)

            if state:
                @use_effect
                def foo():
                    ...

        with self.tree:
            tc()
        self.tree.run_tasks()

        set_state(True)

        with self.assertRaises(HookSequenceError):
            self.tree.run_tasks()

    def test_when_render_less_hooks(self):
        set_state = None

        @functional_component
        def tc():
            nonlocal set_state
            state, set_state = use_state(True)

            if state:
                @use_effect
                def foo():
                    ...

        with self.tree:
            tc()
        self.tree.run_tasks()

        set_state(False)

        with self.assertRaises(HookSequenceError):
            self.tree.run_tasks()

    def test_when_render_different_hooks(self):
        set_state = None

        @functional_component
        def tc():
            nonlocal set_state
            state, set_state = use_state(False)

            if state:
                @use_effect
                def foo():
                    ...
            else:
                use_state()

        with self.tree:
            tc()
        self.tree.run_tasks()

        set_state(True)

        with self.assertRaises(HookSequenceError):
            self.tree.run_tasks()


class UseSelfTest(TreeTestCase):
    def test_use_self(self):
        component_self = None

        @functional_component
        def tc():
            nonlocal component_self
            component_self = use_self()

        with self.tree:
            tc()

        self.tree.run_tasks()

        self.assertIs(component_self, self.tree.root)


class UseStateTest(TreeTestCase):
    def test_use_state(self):
        set_state = None

        @functional_component
        def tc():
            nonlocal set_state
            state, set_state = use_state('default state')

            Component(test_prop=state).insert()

        with self.tree:
            tc()

        self.tree.run_tasks()

        self.assertTrue(callable(set_state))
        self.assertEqual(
            list(self.tree.root.mounted_children())[0].props['test_prop'],
            'default state'
        )

        set_state('new state')
        prev_set_state = set_state

        n_run = self.tree.run_tasks()

        self.assertGreater(n_run, 0)
        self.assertEqual(set_state, prev_set_state)
        self.assertEqual(
            list(self.tree.root.mounted_children())[0].props['test_prop'],
            'new state'
        )


class UseToggleTest(TreeTestCase):
    def test_use_toggle(self):
        toggle = None

        @functional_component
        def tc():
            nonlocal toggle
            state, toggle = use_toggle()

            if state:
                fragment()

        with self.tree:
            tc()

        self.tree.run_tasks()

        self.assertTrue(callable(toggle))
        self.assertEqual(
            len(list(self.tree.root.mounted_children())),
            0
        )

        prev_toggle = toggle
        toggle()

        self.tree.run_tasks()

        self.assertEqual(toggle, prev_toggle)
        self.assertEqual(
            len(list(self.tree.root.mounted_children())),
            1
        )

        prev_toggle = toggle
        toggle()

        self.tree.run_tasks()

        self.assertEqual(toggle, prev_toggle)
        self.assertEqual(
            len(list(self.tree.root.mounted_children())),
            0
        )


class UsePreviousTest(TreeTestCase):
    def test_use_previous(self):
        set_state = None
        track_change = Mock()

        @functional_component
        def tc():
            nonlocal set_state
            state, set_state = use_state('initial state')
            prev = use_previous(state, 'initial prev')

            if prev != state:
                track_change(prev, state)

        with self.tree:
            tc()

        self.tree.run_tasks()

        track_change.assert_called_with('initial prev', 'initial state')
        track_change.reset_mock()

        for _ in range(2):
            self.tree.root.enqueue_update()
            self.tree.run_tasks()

            track_change.assert_not_called()

        set_state('intermediate state')
        set_state('new state')

        self.tree.run_tasks()

        track_change.assert_called_with('initial state', 'new state')
        track_change.reset_mock()

        for _ in range(2):
            self.tree.root.enqueue_update()
            self.tree.run_tasks()

            track_change.assert_not_called()


class UseRefTest(TreeTestCase):
    def test_use_ref(self):
        ref1, ref2 = None, None

        @functional_component
        def fc():
            nonlocal ref1, ref2
            ref1 = use_ref()
            ref2 = use_ref()

        with self.tree:
            fc()
        self.tree.run_tasks()

        self.assertIsInstance(ref1, Ref)
        self.assertIsInstance(ref2, Ref)
        self.assertIsNot(ref1, ref2)

        prev1, prev2 = ref1, ref2
        ref1, ref2 = None, None

        self.tree.root.enqueue_update()
        self.tree.run_tasks()

        self.assertIs(ref1, prev1)
        self.assertIs(ref2, prev2)


class UseEffectTest(TreeTestCase):
    def test_apply_effect(self):
        effect = Mock()

        @functional_component
        def tc():
            @use_effect
            def fx():
                effect()

        with self.tree:
            tc()

        effect.assert_not_called()

        self.tree.run_tasks()

        effect.assert_called_once_with()
        effect.reset_mock()

    def test_rollback_on_unmount(self):
        rollback = Mock()

        @functional_component
        def tc():
            @use_effect
            def fx():
                return rollback

        with self.tree:
            tc()
        self.tree.run_tasks()

        rollback.assert_not_called()

        with self.tree:
            fragment()
        self.tree.run_tasks()

        rollback.assert_called_once_with()

    def test_rollback_and_reapply(self):
        effect, rollback = Mock(), Mock()
        set_state = None

        @functional_component
        def tc():
            nonlocal set_state
            state, set_state = use_state('initial state')

            @use_effect(state)
            def fx():
                effect(state)
                return lambda: rollback(state)

        with self.tree:
            tc()
        self.tree.run_tasks()

        effect.assert_called_once_with('initial state')
        rollback.assert_not_called()
        effect.reset_mock()

        self.tree.root.enqueue_update()
        self.tree.run_tasks()

        effect.assert_not_called()
        rollback.assert_not_called()

        set_state('new state')
        self.tree.run_tasks()
        effect.assert_called_once_with('new state')
        rollback.assert_called_once_with('initial state')


class UseCallbackProxyTest(TreeTestCase):
    def test_use_callback_proxy(self):
        proxy, set_state = None, None
        cb = Mock()

        @functional_component
        def tc():
            nonlocal set_state, proxy
            state, set_state = use_state('initial state')

            proxy = use_callback_proxy(lambda a: cb(state, a))

        with self.tree:
            tc()
        self.tree.run_tasks()

        self.assertTrue(callable(proxy))
        first_proxy = proxy

        proxy('arg 1')

        cb.assert_called_once_with('initial state', 'arg 1')
        cb.reset_mock()

        set_state('new state')
        self.tree.run_tasks()

        self.assertIs(proxy, first_proxy)

        proxy('arg 2')

        cb.assert_called_once_with('new state', 'arg 2')


class UseCallbackTest(TreeTestCase):
    def test_use_callback(self):
        set_state1, set_state2 = None, None
        cb = None
        fn = Mock()

        @functional_component
        def tc():
            nonlocal set_state1, set_state2, cb
            state1, set_state1 = use_state('initial state 1')
            state2, set_state2 = use_state('initial state 2')

            @use_callback(state1)
            def foo(arg):
                fn(state1, state2, arg)

            cb = foo

        with self.tree:
            tc()
        self.tree.run_tasks()

        self.assertTrue(callable(cb))

        cb('arg 1')

        fn.assert_called_once_with('initial state 1', 'initial state 2', 'arg 1')
        fn.reset_mock()

        first_cb = cb
        cb = None

        set_state2('new state 2')
        self.tree.run_tasks()

        self.assertIs(cb, first_cb)

        cb('arg 2')

        fn.assert_called_once_with('initial state 1', 'initial state 2', 'arg 2')
        fn.reset_mock()

        set_state1('new state 1')
        self.tree.run_tasks()

        self.assertIsNot(cb, first_cb)

        cb('arg 3')

        fn.assert_called_once_with('new state 1', 'new state 2', 'arg 3')


class UseMemoTest(TreeTestCase):
    def test_use_memo(self):
        value = None
        set_state1, set_state2 = None, None

        @functional_component
        def tc():
            nonlocal value, set_state1, set_state2
            state1, set_state1 = use_state('initial state 1')
            state2, set_state2 = use_state('initial state 2')

            @use_memo(state1)
            def memo():
                return [state1, state2]

            value = memo

        with self.tree:
            tc()
        self.tree.run_tasks()

        self.assertEqual(
            value,
            ['initial state 1', 'initial state 2']
        )
        first_value = value
        value = None

        set_state2('new state 2')
        self.tree.run_tasks()

        self.assertIs(first_value, value)

        set_state1('new state 1')
        self.tree.run_tasks()

        self.assertIsNot(value, first_value)
        self.assertEqual(
            value,
            ['new state 1', 'new state 2']
        )
