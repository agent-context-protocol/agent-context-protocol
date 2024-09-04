from base import BaseNode


class MainTranslatorNode(BaseNode):
    def __init__(self, node_name, system_prompt = None):
        super().__init__(node_name, system_prompt)
        self.clusters = {}

    def setup(self):
        # Logic to create and initialize local translator instances
        # We can use self.chat_history to provide context
        pass