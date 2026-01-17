class BVECommandGenerator:
    @staticmethod
    def make_command(track_position, command, *args):
        args_str = ";".join(str(a) for a in args)
        return f"{track_position},.{command} {args_str};"