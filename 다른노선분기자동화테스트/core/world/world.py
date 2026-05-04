class World:
    """ECS 월드: 엔티티, 컴포넌트, 시스템을 관리"""
    def __init__(self):
        self.entities = {}
        self.components = {}
        self.systems = []

    def add_entity(self, name, entity):
        self.entities[name] = entity

    def add_component(self, name, component):
        self.components[name] = component

    def add_system(self, system):
        self.systems.append(system)

    def run(self):
        """등록된 시스템을 순차 실행"""
        for system in self.systems:
            system.execute(self.entities, self.components)
