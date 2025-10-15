class ConstructionCostCalculator:
    def __init__(self, 
                 earth_cost=8620,
                 bridge_cost=24574,
                 tunnel_cost=15784,
                 station_cost=63973,
                 rail_cost=978,
                 electric_cost=461,
                 signal_cost=601,
                 communication_cost=466):
        self.earth_cost = earth_cost
        self.bridge_cost = bridge_cost
        self.tunnel_cost = tunnel_cost
        self.station_cost = station_cost
        self.rail_cost = rail_cost
        self.electric_cost = electric_cost
        self.signal_cost = signal_cost
        self.communication_cost = communication_cost

    def calculate_total(self, 
                        total_earth_length, 
                        total_bridge_length, 
                        total_tunnel_length, 
                        linestring_length,
                        num_stations=3):
        total = (
            self.earth_cost * total_earth_length +
            self.bridge_cost * total_bridge_length +
            self.tunnel_cost * total_tunnel_length +
            self.station_cost * num_stations +
            self.rail_cost * linestring_length +
            self.electric_cost * linestring_length +
            self.signal_cost * linestring_length +
            self.communication_cost * linestring_length
        )
        return total
