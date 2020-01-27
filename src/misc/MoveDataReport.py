class MoveDataReport:
    def __init__(self, name, true_false_list):
        self.name = name
        self.start_stop_pairs = self.process_list(true_false_list)

    def process_list(self, true_false_list):
        total_frames = len(true_false_list)
        start_stop_pairs = []
        start = -1
        stop = -1
        for i, data_true in enumerate(reversed(true_false_list)):
            if start < 0 and data_true:
                start = i + 1
            elif start >= 0 and not data_true:
                stop = i
                start_stop_pairs.append((start, stop))
                start = -1
                stop = -1

        if stop < 0 and start >= 0:
            start_stop_pairs.append((start, ''))

        return start_stop_pairs

    def is_present(self):
        return len(self.start_stop_pairs) > 0

    def total_present(self):
        total = 0
        for pair in self.start_stop_pairs:
            total += pair[1] - pair[0] + 1
        return total

    def __repr__(self):
        repr = self.name + ": "
        for pair in self.start_stop_pairs:
            repr += '{}~{} '.format(pair[0], pair[1])
        return repr
