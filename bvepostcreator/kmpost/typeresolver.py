class KMPostTypeResolver:
    @staticmethod
    def resolve(station, interval):
        if station % 1000 == 0:
            return 'km표'
        elif station % interval == 0:
            return 'm표'
        return ''
