x = 10
def change_x():
	global x
	x += 1
change_x()
print("x:",x)