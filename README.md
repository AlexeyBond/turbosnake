# turbosnake - a react.js-like framework for ui in python

## Motivation

There are lots of nice graphical applications written in python. But code that creates UI (at least in simple examples I
could find and in few projects I tried to contribute to) looks like some sort of imperative mess. And it gets even
uglier when UI should be changed dynamically. So, I decided to try to reproduce the declarative approach which I am used
to as a professional web-developer.

## Installing

```shell
$ pip install turbosnake
```

## Syntax

Unlike JavaScript frameworks with JSX, we cannot just modify Python's syntax for our purposes. Instead, turbosnake uses
unmodified Python's syntax to represent its concepts.

### Instantiating components

Instead of JSX's `<Component ... />` turbosnake uses a plain function call:

```python
from turbosnake import Component

...
Component(...)
```

In most cases, return value of such calls is useless. The main effect of such call is a component being appended to a
list in specific runtime context. Calls of components outside of proper runtime context are prohibited and will cause
error.

### Nesting components

Children are added to a component using `with` operator:

```python
with Component1(...):
    Component11(...)
    Component12(...)
```

this fragment of code is kinda equivalent to the following JSX:

```jsx
<Component1 ...>
    <Component11 .../>
    <Component12 .../>
</Component1>
```

but unlike it, any loops and conditions are allowed within body of `with` operator. Components that support nesting
implement context provider interface. When used in `with` operator they substitute previously mentioned runtime context
with the one that adds all created components to list of their children.

### Functional components

The easiest way to compose few components is to create a functional component. In some simple cases (component doesn't
use hooks or is always rendered constant number of times within it's parent) a plain function can serve as a functional
component:

```python
def foo(**props):
    with Component1():
        Component2(**props)


...

foo(...)
```

But a function can be converted into a full-fledged component with its own state using `functional_component` decorator:

```python
from turbosnake import functional_component

...


@functional_component
def foo(**props):
    with Component1():
        Component2(**props)


...

foo(...)
```

Depending on function signature and settings passed to the decorator, it may add (or don't add) support for nesting and
hooks.

### Hooks

Hooks are supported in functional components (if not disabled explicitly) and in components
inheriting `ComponentWithHooks`. Some of implemented hooks are: `use_toggle`, `use_state`, `use_memo`, `use_effect`
, `use_callback`, `use_previous`, `use_ref`, `use_callback_proxy`, `use_self`.

Hooks that accept a function can be used as decorators on a local function:

```python
from turbosnake import functional_component, use_callback

...


@functional_component
def foo():
    ...

    @use_callback([...])
    def callback():
        ...

    ...
```

## UI

Core of turbosnake isn't bound to any UI library or framework. With some effort applied, it can be used with any UI
library or even for purposes different from user interface rendering.

Package `turbosnake.ttk` provides adapters for tkinter (mostly ttk) UI components. For examples
see [TODO-list application example](https://github.com/AlexeyBond/turbosnake/blob/master/examples/todo.py).
