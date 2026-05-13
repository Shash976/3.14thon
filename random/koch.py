import turtle

def draw_koch_segment(t, length, depth):
    if depth == 0:
        t.forward(length)
    else:
        length /= 3.0
        draw_koch_segment(t, length, depth-1)
        t.left(60)
        draw_koch_segment(t, length, depth-1)
        t.right(120)
        draw_koch_segment(t, length, depth-1)
        t.left(60)
        draw_koch_segment(t, length, depth-1)

def draw_koch_snowflake(t, length, depth):
    for i in range(3):
        draw_koch_segment(t, length, depth)
        t.right(120)

window = turtle.Screen()
window.bgcolor("white")

# Function to draw multiple Koch snowflakes
def draw_multiple_snowflakes(number_of_snowflakes, length, depth):
    for i in range(number_of_snowflakes):
        flake = turtle.Turtle()
        flake.speed("fastest")  # Set drawing to the fastest speed
        # Position the turtle for each snowflake
        flake.penup()
        flake.goto(i * 100 - 200, i * 50 - 200)  # Adjust starting positions as needed
        flake.pendown()
        draw_koch_snowflake(flake, length, depth)
        flake.hideturtle()

# Draw multiple Koch snowflakes
draw_multiple_snowflakes(5, 100, 3)  # Adjust the number of snowflakes, size, and detail level

turtle.done()
