from unittest import TestCase
from unittest.mock import Mock

from turbosnake import event_prop_invoker


class EventPropInvokerTest(TestCase):
    def setUp(self) -> None:
        class ComponentStub:
            ...

        self.target = ComponentStub()
        self.target.props = {}

    def test_prop_missing(self):
        fn = event_prop_invoker(self.target, 'on_event')

        self.assertTrue(callable(fn))

        with self.assertRaises(KeyError):
            fn()

    def test_invoke_prop(self):
        fn = event_prop_invoker(self.target, 'on_event')
        cb = Mock(return_value='mock return value')
        self.target.props = {'on_event': cb}
        ret = fn('arg1', 2, kwa='kwa')

        self.assertEqual(ret, 'mock return value')
        cb.assert_called_with('arg1', 2, kwa='kwa')
