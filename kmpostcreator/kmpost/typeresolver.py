class KMPostTypeResolver:
    def __init__(self, interval):
        self.interval = interval

    def resolve(self, station):
        if station % 1000 == 0:
            return 'km표'
        elif station % self.interval == 0:
            return 'm표'
        return ''
