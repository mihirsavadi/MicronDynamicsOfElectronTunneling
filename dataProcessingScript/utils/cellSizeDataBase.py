# Mihir Savadi
# 24th February 2021

# this is a dictionary mapping the array coordinates (not a complete coordinate) to the cell size. This is
# predetermined from the wafer architecture we've been using, which is unlikely to change at any point in the near
# future.
# TODO: This is incomplete! Need to include sizes for all the arrays in the grid
cellSizes = {
    '(0,0)' : '10um',
    '(0,1)' : '10um',
    '(0,2)' : '10um',
    '(0,7)' : '10um',
    '(0,6)' : '10um',
    '(0,7)' : '10um',
    '(0,8)' : '10um',

    '(1,0)' : '10um',
    '(1,1)' : '10um',
    '(1,2)' : '10um',

    '(2,0)' : '15um',
    '(2,1)' : '20um',
}