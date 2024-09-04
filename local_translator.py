from base import BaseNode

class LocalTranslatorNode(BaseNode):
    def __init__(self, node_id, panel_description):
        super().__init__(node_id)
        self.panel_description = panel_description
        self.workflow = None