from components import Tree


class TestTree(Tree):
    def __init__(self):
        super().__init__()
        self.__callbacks = []

    def schedule_task(self, callback):
        self.__callbacks.append(callback)

    def run_tasks(self):
        while len(self.__callbacks):
            self.__callbacks.pop(0)()
