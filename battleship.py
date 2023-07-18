map = [
        [0,0,0,1],
        [1,0,1,0],
        [0,0,0,0],
        [0,1,0,0]
        ]

hits = 0
turns = 0
while hits < 4:
    row = int(input("Choose Co-ordinates\nRow (between 0 and 3): "))
    column = int(input("Column (between 0 & 3): "))
    if map[row][column] == 1:
        hits += 1
        map[row][column] = 0
        print(f'HIT! You have hit {hits} ships')
    else:
        print('Miss')
    turns += 1
print(f'You beat the game in {turns} chances')
