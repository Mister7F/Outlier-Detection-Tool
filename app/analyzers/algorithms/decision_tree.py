import math
import numpy as np


class Tree:
    def __init__(self, data, feature_type, max_depth=3, depth=0):
        '''
        - data (np.ndarray) : 2D array - rows: items - cols: features
                              Last column is the featue we want to classify
        - type (list)       : feature type 'enum' or 'float'
        '''
        self.dataset = data
        self.feature_type = feature_type
        self.depth = depth

        self.rule_val = None
        self.rule_col = None

        self.group_1 = None
        self.group_2 = None

        self.childs = []

        self._check_parameter()

        self.build_tree()

        if (depth < max_depth and self.group_1.size
           and self.group_2.size and np.unique(data[:, -1]).size > 1):

            child_1 = Tree(self.group_1, feature_type, max_depth, depth+1)
            child_2 = Tree(self.group_2, feature_type, max_depth, depth+1)

            self.childs = [child_1, child_2]

    def _check_parameter(self):
        if len(self.feature_type) != self.dataset.shape[1]:
            raise Exception(
                "Error, feature_type does'nt have the same size as data")

        if self.feature_type[-1] != 'enum':
            raise Exception(
                "Error, last feature (label) needs the 'enum' type'")

        for i, f in enumerate(self.feature_type):
            if f == 'enum':
                continue
            try:
                self.dataset[:, i].mean()
            except Exception:
                raise Exception('Float type needed')

    def impurity(self, debug=False):
        values_1, count_1 = np.unique(self.group_1[:, -1], return_counts=True)
        values_2, count_2 = np.unique(self.group_2[:, -1], return_counts=True)

        if not count_1.sum() or not count_2.sum():
            return float('inf')

        if count_1.size == 1:
            count_1 = np.append(count_1, [0])

        if count_2.size == 1:
            count_2 = np.append(count_2, [0])

        freq_1 = count_1 / count_1.sum()
        freq_2 = count_2 / count_2.sum()

        gini_1 = 1 - np.square(freq_1).sum()
        gini_2 = 1 - np.square(freq_2).sum()

        return (
            (gini_1 * count_1.sum() + gini_2 * count_2.sum())
            / self.dataset.shape[0]
        )

    def split_data(self):
        if self.feature_type[self.rule_col] == 'enum':
            self.group_1 = self.dataset[
                self.dataset[:, self.rule_col] == self.rule_val
            ]
            self.group_2 = self.dataset[
                self.dataset[:, self.rule_col] != self.rule_val
            ]
        else:
            self.group_1 = self.dataset[
                self.dataset[:, self.rule_col] >= self.rule_val
            ]
            self.group_2 = self.dataset[
                self.dataset[:, self.rule_col] < self.rule_val
            ]

    def build_tree(self):

        min_impurity = float('inf')
        best_rule = None

        for col, f in enumerate(self.feature_type[:-1]):

            self.rule_col = col

            if f == 'enum':
                for v in np.unique(self.dataset[:, col]):
                    self.rule_val = v

                    self.split_data()

                    _imp = self.impurity()

                    if _imp < min_impurity:
                        min_impurity = _imp
                        best_rule = (v, col)
            else:
                min = self.dataset[:, col].min()
                max = self.dataset[:, col].max()

                for j in range(100):
                    v = (max - min) * (j/100) + min
                    self.rule_val = v

                    self.split_data()

                    _imp = self.impurity()
                    if _imp < min_impurity:
                        min_impurity = _imp
                        best_rule = (v, col)

        if not best_rule:
            return

        self.rule_val, self.rule_col = best_rule

        self.split_data()

    def predict(self, item):

        if not self.childs:
            values, counts = np.unique(self.dataset[:, -1], return_counts=True)

            return values[np.argsort(counts)[-1]]

        if self.feature_type[self.rule_col] == 'enum':
            if item[self.rule_col] == self.rule_val:
                return self.childs[0].predict(item)
            else:
                return self.childs[1].predict(item)
        else:
            if item[self.rule_col] >= self.rule_val:
                return self.childs[0].predict(item)
            else:
                return self.childs[1].predict(item)

    def __str__(self):

        val, count = np.unique(self.dataset[:, -1], return_counts=True)
        label = val[np.argsort(count)[-1]]

        string = ('    ' if self.depth else '') + \
            '[%s, %s %%] ' % (label, str(max(count)*100/count.sum())[:3])
        string += 'Rule: ' + str(self.rule_val) + ' on col %i' % self.rule_col

        for c in self.childs:
            string += '\n' + '      ' * self.depth + '  ' + str(c)

        return string
