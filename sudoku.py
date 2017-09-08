import sys
from itertools import chain


class DLXNode:
    __slots__ = ('hdr', 'up', 'left', 'right', 'down', 'starts_row')

    def __init__(self, h = None, l = None, r = None, u = None, d = None):
        self.hdr = h
        self.up = u
        self.left = l
        self.right = r
        self.down = d
        self.starts_row = False


class DLXHdr:
     __slots__ = ('col_num', 'left', 'right', 'up', 'down', 'size')

     def __init__(self, c = None, l = None, r = None, u = None, d = None):
         self.col_num = c
         self.up = u
         self.left = l
         self.right = r
         self.down = d
         self.size = 0


class DLXSolver:
    def __init__(self, num_cols, rows):
        nodes = [DLXHdr(None, i-1, i+1) if i == 0 else DLXHdr(i-1, i-1, i+1)
                 for i in range(num_cols + 1)]
        nodes[num_cols].right = 0
        nodes[0].left = num_cols
        self._nodes = nodes
        self._num_cols = num_cols

        bottoms = [i + 1 for i in range(num_cols)]
        for row in rows:
            self._add_row(bottoms, row)
        self._finish(bottoms)

        self.solve_count = 0

    def _add_row(self, bottoms, row):
        hidx = len(self._nodes)

        for col_num in row:
            idx = len(self._nodes)
            node = DLXNode(col_num, idx - 1, idx + 1, bottoms[col_num])
            self._nodes.append(node)
            self._nodes[bottoms[col_num]].down = idx
            bottoms[col_num] = idx
            self._nodes[col_num + 1].size += 1

        self._nodes[idx].right = hidx
        self._nodes[hidx].left = idx
        self._nodes[hidx].starts_row = True

    def _finish(self, bottoms):
        idx = 1
        while idx != 0:
            self._nodes[idx].up = bottoms[idx - 1]
            self._nodes[bottoms[idx - 1]].down = idx
            idx = self._nodes[idx].right

        for node in self._nodes:
            node.left = self._nodes[node.left]
            node.right = self._nodes[node.right]
            if node.up is not None:
                node.up = self._nodes[node.up]
            if node.down is not None:
                node.down = self._nodes[node.down]

        for idx in range(self._num_cols + 1, len(self._nodes)):
            node = self._nodes[idx]
            if node.hdr is not None:
                node.hdr = self._nodes[node.hdr + 1]

    def _cover(self, header):
        header.right.left = header.left
        header.left.right = header.right
        rownode = header.down
        while rownode is not header:
            colnode = rownode.right
            while colnode is not rownode:
                colnode.hdr.size -= 1
                colnode.up.down = colnode.down
                colnode.down.up = colnode.up
                colnode = colnode.right
            rownode = rownode.down

    def _uncover(self, header):
        rownode = header.up
        while rownode is not header:
            colnode = rownode.left
            while colnode is not rownode:
                colnode.hdr.size += 1
                colnode.up.down = colnode
                colnode.down.up = colnode
                colnode = colnode.left
            rownode = rownode.up

        header.right.left = header
        header.left.right = header

    def _choose_column(self):
        minsize = len(self._nodes)
        node = None
        header = self._nodes[0]
        colnode = header.right
        while colnode != header:
            if colnode.size < minsize:
                node = colnode
                minsize = colnode.size
            colnode = colnode.right
        return node

    def _get_row(self, rownode):
        while not rownode.starts_row:
            rownode = rownode.left
        row = [rownode.hdr.col_num]
        colnode = rownode.right
        while colnode is not rownode:
            row.append(colnode.hdr.col_num)
            colnode = colnode.right
        return row

    def _solve(self, printer, solrows, solnodes, k):
        self.solve_count += 1

        if self._nodes[0].right is self._nodes[0]:
            self._finished = not printer(chain(solrows, (self._get_row(r)
                                                         for r in solnodes)))
            return
        header = self._choose_column()
        self._cover(header)

        rownode = header.down
        while rownode is not header:
            solnodes.append(rownode)
            colnode = rownode.right
            while colnode is not rownode:
                self._cover(self._nodes[colnode.hdr.col_num + 1])
                colnode = colnode.right

            self._solve(printer, solrows, solnodes, k + 1)

            colnode = rownode.left
            while colnode is not rownode:
                self._uncover(self._nodes[colnode.hdr.col_num + 1])
                colnode = colnode.left

            solnodes.pop()
            if self._finished: break

            rownode = rownode.down
        self._uncover(header)

    def solve(self, printer, solrows):
        self._finished = False
        rows = []
        for row in solrows:
            rows.append(list(row))
            for col_num in row:
                self._cover(self._nodes[col_num + 1])

        self._solve(printer, rows, [], 0)

        for row in rows[::-1]:
            for col_num in row[::-1]:
                self._uncover(self._nodes[col_num + 1])


def sudoku_sparse_matrix(size, boxes):
    for num in range(size):
        for row in range(size):
            for col in range(size):
                yield sudoku_sparse_row(size, boxes, num, row, col)


def sudoku_sparse_row(size, boxes, num, row, col):
    s2 = size * size
    return (row * size + col,
             s2 + num * size + col,
             s2 + s2 + num * size + row,
             s2 + s2 + s2 + num * size + boxes(row, col))


def reconstruct(size, solrows):
    s2 = size * size
    grid = [[0 for col in range(size)] for row in range(size)]
    for srow in solrows:
        num = (srow[1] - s2) // size
        col = (srow[1] - s2) % size
        row = (srow[2] - (s2 + s2)) % size
        grid[row][col] = num + 1
    return grid


# TODO other than 9x9?
def boxes3x3(row, col):
    return ((row // 3) * 3) + (col // 3)

def rows_from_txt(line):
    for row in range(9):
        for col in range(9):
            c = line[row*9 + col]
            if c == '.': continue
            num = ord(c) - ord('0') - 1
            yield sudoku_sparse_row(9, boxes3x3, num, row, col)


if __name__ == '__main__':
    def printer(solrows):
        grid = reconstruct(9, solrows)
        for row in grid:
            print(''.join(map(str, row)), end='')
        print()
        return True

    s = DLXSolver(324, sudoku_sparse_matrix(9, boxes3x3))
    for line in sys.stdin.readlines():
        s.solve(printer, rows_from_txt(line))
        print()
