from ._components import Component


def event_prop_invoker(self: Component, prop_name):
    """Creates a function that invokes event handler stored in given property of given component.

    Resulting function reads property on every invocation, so it remains valid after the property is changed.

    When property is missing or falsy, nothing happens on invocation of resulting function.

    :param self: component instance
    :param prop_name: name of a property containing event handler
    :return: the function, as described above
    """

    def _event_prop_invoker(*args, **kwargs):
        try:
            cb = self.props[prop_name]
        except KeyError:
            return

        return cb(*args, **kwargs)

    return _event_prop_invoker
