Objects of `turbosnake.Tree` serve as root of turbosnake application tree.

Unlike components, `Tree` doesn't have any state and doesn't initiate any updates. The `Tree` may have one
child `Component` that is called tree root. The root is added to tree using `with` operator:

```python
from turbosnake import Tree

...
my_tree: Tree = ...

with my_tree:
    ...  # Render EXACTLY ONE component
```

Root can always be replaced the same way it was added. Note that it will always unmount current root component and
render new root component from scratch even if the new root is of the same type and has equal props.

The root component of a tree can always be accessed using it's `root` property. For any mounted component the tree it is
mounted to is accessible through it's `tree` property:

```python
from turbosnake import Tree, Component

...
my_tree: Tree = ...

root: Component = my_tree.root

assert root.tree is my_tree
```

## Event loop

`Tree` provides event loop for underlying components.

Most of component-related tasks are executed through queues. By default, there are two of them - `update` and `effect`.
Component updates (including re-rendering of children), caused by changes in properties or state of components are
executed in`update` queue. Other side effects (like ones caused by `use_effect` hooks) are executed in `effect` queue.
Tree decides in which order tasks are executed depending on which queue they are added.

Tasks are enqueued for execution using `enqueue_task` method:

```python
from turbosnake import Tree, Component

...
my_tree: Tree = ...


def my_task():
    ...


my_tree.enqueue_task('effect', my_task)
```

The task can also be scheduled for delayed execution using `schedule_delayed_task`:

```python
from turbosnake import Tree, Component

...
my_tree: Tree = ...


def my_task():
    ...  # Will be executed 1 second later


my_tree.schedule_delayed_task(1000, my_task)
```

## Testing

For testing purposes there is implementation of `Tree` called `turbosnake.test_helpers.TestTree` and `TestCase` subclass
`turbosnake.test_helpers.TreeTestCase` that initializes instance of `TestTree` and provides some additional helper
methods.

`TestTree` emulates event loop by running all enqueued tasks when `run_tasks` method is called.
`run_tasks` executes all enqueued tasks until there remains no more tasks.

`TestTree` currently doesn't support delayed task execution.
