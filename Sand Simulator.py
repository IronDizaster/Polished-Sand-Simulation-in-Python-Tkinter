import random
import time
from tkinter import *
from tkinter import messagebox
import tkinter.font as tkfont

def find_divisors_of_numbers(num_1: int, num_2: int) -> list[int]:
    divisors = []
    smaller_number = min(num_1, num_2)
    for i in range(1, smaller_number + 1):
        if num_1 % i == 0 and num_2 % i == 0:
            divisors.append(i)
    return divisors

root = Tk()
root.attributes('-fullscreen', True)
WINDOW_WIDTH = 1250
WINDOW_HEIGHT = 900
target_fps = 80

WINDOW_WIDTH = root.winfo_screenwidth()
WINDOW_HEIGHT = root.winfo_screenheight()
bg_color = '#141414'
canvas_color = 'LightSkyBlue'
title = 'Sand Simulator'

zoom_levels = [x for x in range(8, 30, 2)]

zoom_index = 1

num_of_rows = WINDOW_WIDTH // zoom_levels[zoom_index]
num_of_col = WINDOW_HEIGHT // zoom_levels[zoom_index]

pixel_radius = zoom_levels[zoom_index]

squares = []
saved_positions = []
colors = ['#e1bf92', '#e7c496', '#eccca2', '#f2d2a9', '#f6d7b0']

edge_padding = 10 # how many pixels of empty space around the movable canvas
padding = 10
font_family = 'Arial'
font_size = 15

# bottom right outer edge : window_width - pixel_radius_global * edge_padding
# bottom outer edge : window_height - pixel_radius_global * edge_padding
# top left outer edge : 0 - pixel_radius_global * edge_padding
# top outer edge: 0 - pixel_radius_global * edge_padding

top_left_edge = [0, 0]
bottom_right_edge = [WINDOW_WIDTH, WINDOW_HEIGHT]

grid_on = False # used to determine whether to show/hide grid by pressing G
time_stop = False # used to stop/start simulation in stop time function
is_drawing = False # used to determine whether the user is holding down mouse1 
show_help_text = True # when true, show text which tells the user about the controls
event_var = 0 # used as a global "event" variable to keep track of mouse positions without needing to pass it as an argument (bad practice)


canvas = Canvas(root, width = WINDOW_WIDTH, height = WINDOW_HEIGHT, bg = bg_color)
canvas.pack()

def center_screen():
    screen_width = root.winfo_screenwidth()  # Width of the user screen
    screen_height = root.winfo_screenheight() # Height of the user screen

    # Starting X & Y window positions:
    x = (screen_width / 2) - (WINDOW_WIDTH / 2)
    y = (screen_height / 2) - (WINDOW_HEIGHT / 2)

    root.geometry('%dx%d+%d+%d' % (WINDOW_WIDTH, WINDOW_HEIGHT, x, y))
    tm = ' (IronDizaster ©)'
    root.title(title + tm)

def create_grid_lines(color = 'black'):
    x = top_left_edge[0]
    y = top_left_edge[1]
    for i in range(num_of_rows):
        canvas.create_line(x, y, x, bottom_right_edge[1], fill=color, tag='grid_line')
        x += pixel_radius
    x = top_left_edge[0]
    for j in range(num_of_col):
        canvas.create_line(x, y, bottom_right_edge[0], y, fill=color, tag='grid_line')
        y += pixel_radius
    canvas.itemconfigure('grid_line', state='hidden')
    create_edge()
    move_canvas(2, -2)

def create_edge(color = 'red'):
    canvas.create_rectangle(top_left_edge[0], 
                            top_left_edge[1], 
                            bottom_right_edge[0], 
                            bottom_right_edge[1], width=2, outline=color, tag='edge', fill=canvas_color)
    canvas.tag_lower('edge')

def move_canvas(x_offset, y_offset):
    canvas.move('square', x_offset, y_offset)
    canvas.move('edge', x_offset, y_offset)
    canvas.move('grid_line', x_offset, y_offset)
    update_canvas_position()

def find_distance_to_nearest_grid_space(x, y, divisor) -> tuple:
    if x % divisor == 0 and y % divisor == 0: return (0, 0) # no need to move
    finding_range = 1
    x_range = -finding_range
    y_range = -finding_range
    square_circumference = (finding_range * 3 - finding_range) * 2 # outer-most pixels of the searching square - 
                                                                   # only needs to be multiplied by 2 and not 4 because opposite sides can be checked in each iteration

    while finding_range < 500: # after 500 iterations its safe to say something went terribly wrong
        for i in range(square_circumference):
            # check for result
            if (x + x_range) % divisor == 0 and (y + y_range) % divisor == 0: 
                return (x_range, y_range)
            # check for opposite result
            if (x - x_range) % divisor == 0 and (y - y_range) % divisor == 0: 
                return (-x_range, -y_range)
            if x_range < finding_range:
                x_range += 1
            else:
                y_range += 1

        finding_range += 1
        square_circumference = (finding_range * 3 - finding_range) * 2
        x_range = -finding_range
        y_range = -finding_range

def scale_canvas(x_offset, y_offset, scale_multiplier):
    canvas.scale('edge', x_offset, y_offset, scale_multiplier, scale_multiplier)
    canvas.scale('grid_line', x_offset, y_offset, scale_multiplier, scale_multiplier)
    canvas.scale('square', x_offset, y_offset, scale_multiplier, scale_multiplier)
    update_canvas_position()
    
     
    # the following if statement is required in order to fix an annoying bug where upon zooming in, some squares (pixels) would get randomly displaced by a single pixel, in a seemingly
    # random direction. 
    # It searches for a nearest pixel which is divisible by the pixel radius (grid space), finds out the distance between that pixel and the square's top left corner, and moves the square
    # that distance in order to offset this seemingly random displacement.
    # NOTE: Most likely there is a faster & smarter solution out there (but idfc)
    if len(saved_positions) != 0:
        for pos in saved_positions:
            x_y = find_distance_to_nearest_grid_space(pos[0] - top_left_edge[0], pos[1] - top_left_edge[1], pixel_radius)
            x_range = x_y[0]
            y_range = x_y[1]
            canvas.move(pos[2], x_range, y_range)
            pos[0] = round(canvas.coords(pos[2])[0])
            pos[1] = round(canvas.coords(pos[2])[1])

    if len(squares) != 0:
        for square in squares:
            x_y = find_distance_to_nearest_grid_space(square[0] - top_left_edge[0], square[1] - top_left_edge[1], pixel_radius)
            x_range = x_y[0]
            y_range = x_y[1]
            canvas.move(square[2], x_range, y_range)
            square[0] = round(canvas.coords(square[2])[0])
            square[1] = round(canvas.coords(square[2])[1])
        

def update_canvas_position():
    top_left_edge[0] = round(canvas.coords('edge')[0])
    top_left_edge[1] = round(canvas.coords('edge')[1])

    bottom_right_edge[0] = round(canvas.coords('edge')[2])
    bottom_right_edge[1] = round(canvas.coords('edge')[3])

    for square in squares:
        square[0] = round(canvas.coords(square[2])[0]) 
        square[1] = round(canvas.coords(square[2])[1])

    for pos in saved_positions:
        # x_y = find_distance_to_nearest_grid_space(pos[0] - top_left_edge[0], pos[1] - top_left_edge[1], pixel_radius)
        # x_range = x_y[0]
        # y_range = x_y[1]
        # canvas.move(pos[2], x_range, y_range)
        pos[0] = round(canvas.coords(pos[2])[0])  
        pos[1] = round(canvas.coords(pos[2])[1])
        

def zoom_in_or_out(event):
    global pixel_radius
    global zoom_index
    previous_pixel_radius = pixel_radius
    mouse_wheel_dir = event.delta

    # Update zoom index based on scroll up/down
    if mouse_wheel_dir > 0: # up
        if zoom_index != len(zoom_levels) - 1:
            zoom_index += 1

    elif mouse_wheel_dir < 0: # down
        if zoom_index != 1:
            zoom_index -= 1
    
    # update pixel radius & find out the zoom coefficient
    pixel_radius = zoom_levels[zoom_index]
    zoom_coefficient = pixel_radius / previous_pixel_radius
    
    if zoom_coefficient != 1: # if not equal to 1 => user zoomed in/out
        x = round(canvas.canvasx(event.x), -2)
        y = round(canvas.canvasy(event.y), -2)
        scale_canvas(x, y, zoom_coefficient)
        create_preview_square(event)
        if zoom_index == 1:
            canvas.configure(scrollregion = (top_left_edge[0], 
                                             top_left_edge[1], 
                                             bottom_right_edge[0], 
                                             bottom_right_edge[1]))
        else:
            canvas.configure(scrollregion = (top_left_edge[0] - pixel_radius * edge_padding, 
                                             top_left_edge[1] - pixel_radius * edge_padding, 
                                             bottom_right_edge[0] + pixel_radius * edge_padding, 
                                             bottom_right_edge[1] + pixel_radius * edge_padding))
    update_sim_speed_text()
    if show_help_text == True:
        initialize_text()        

def draw(mouse):
    global pixel_radius
    create_preview_square(mouse)
    # top left edge [0] and [1] are the offsets caused by dragging the screen, hence why they are added to mouse pos x & y, and subtracted from pixel x & y
    mouse_x = canvas.canvasx(mouse.x) - top_left_edge[0]
    mouse_y = canvas.canvasy(mouse.y) - top_left_edge[1]

    pixel_x = ((mouse_x // pixel_radius) * pixel_radius) + top_left_edge[0]
    pixel_y = ((mouse_y // pixel_radius) * pixel_radius) + top_left_edge[1]

    outline_width = 0
    if grid_on == 1:
        outline_width = 1

    if is_position_valid(pixel_x, pixel_y): # this is to prevent drawing overlapping squares (pixels) and drawing out of border
        square_id = canvas.create_rectangle(pixel_x, pixel_y, pixel_x + pixel_radius, pixel_y + pixel_radius, fill=random.choice(colors), tag='square', width=outline_width)
        squares.append([pixel_x, pixel_y, square_id])

def is_position_valid(pixel_x, pixel_y) -> bool:
    '''checks whether the clicked pixel is within borders and doesn't already contain a square'''
    if pixel_x < top_left_edge[0] or pixel_x > bottom_right_edge[0] - pixel_radius or pixel_y < top_left_edge[1] or pixel_y > bottom_right_edge[1] - pixel_radius:
        return False # position not within borders
    for square in squares:
        if (square[0] == pixel_x) and (square[1] == pixel_y):
            return False # position is invalid - squares would overlap
    for pos in saved_positions:
        if pos[0] == pixel_x and pos[1] == pixel_y:
            return False
    return True

def is_position_grounded(pixel_x, pixel_y) -> bool:
    '''checks whether the checked pixel contains a grounded square or border'''
    if (pixel_x < top_left_edge[0] or pixel_x > bottom_right_edge[0] - pixel_radius or pixel_y < top_left_edge[1] or pixel_y > bottom_right_edge[1] - pixel_radius):
        return True
    else:
        for pos in saved_positions:
            if (pos[0] == pixel_x and pos[1] == pixel_y):
                return True
    return False


def create_preview_square(mouse):
    global event_var
    event_var = mouse
    canvas.delete('preview')
    outline_width = 0
    if grid_on:
        outline_width = 1
    # top left edge [0] and [1] are the offsets caused by dragging the screen, hence why they are added to mouse pos x & y, and subtracted from pixel x & y
    mouse_x = canvas.canvasx(mouse.x) - top_left_edge[0]
    mouse_y = canvas.canvasy(mouse.y) - top_left_edge[1]

    pixel_x = ((mouse_x // pixel_radius) * pixel_radius) + top_left_edge[0]
    pixel_y = ((mouse_y // pixel_radius) * pixel_radius) + top_left_edge[1]

    if is_position_valid(pixel_x, pixel_y):
        canvas.create_rectangle(pixel_x, pixel_y, pixel_x + pixel_radius, pixel_y + pixel_radius, fill=random.choice(colors), width=outline_width, tag='preview')
    
    if grid_on:
        # show pixel coordinates next to preview square if grid is on:
        x_pixel_coord = round((pixel_x - top_left_edge[0]) // pixel_radius)
        y_pixel_coord = round((pixel_y - top_left_edge[1]) // pixel_radius)

        canvas.create_text(pixel_x + pixel_radius / 2, 
                           pixel_y - pixel_radius / 2 + 1, 
                           text=f'[{x_pixel_coord}, {y_pixel_coord}]', 
                           font=f'{font_family} {round(font_size / 1.5)} bold',
                           fill='black',
                           tag='preview')
        
        canvas.create_text(pixel_x + pixel_radius / 2 + 1, 
                           pixel_y - pixel_radius / 2, 
                           text=f'[{x_pixel_coord}, {y_pixel_coord}]', 
                           font=f'{font_family} {round(font_size / 1.5)} bold',
                           fill='black',
                           tag='preview')

        canvas.create_text(pixel_x + pixel_radius / 2 - 1, 
                           pixel_y - pixel_radius / 2, 
                           text=f'[{x_pixel_coord}, {y_pixel_coord}]', 
                           font=f'{font_family} {round(font_size / 1.5)} bold',
                           fill='black',
                           tag='preview')
        
        canvas.create_text(pixel_x + pixel_radius / 2, 
                           pixel_y - pixel_radius / 2 - 1, 
                           text=f'[{x_pixel_coord}, {y_pixel_coord}]', 
                           font=f'{font_family} {round(font_size / 1.5)} bold',
                           fill='black',
                           tag='preview')
        
        canvas.create_text(pixel_x + pixel_radius / 2, 
                           pixel_y - pixel_radius / 2, 
                           text=f'[{x_pixel_coord}, {y_pixel_coord}]', 
                           font=f'{font_family} {round(font_size / 1.5)} bold',
                           fill='white',
                           tag='preview')

def scan_mark(event):
    if zoom_index != 1:
        canvas.scan_mark(event.x, event.y)

def drag(event):
    if zoom_index != 1:
        canvas.scan_dragto(event.x, event.y, 1)
        if show_help_text == True: initialize_text()
        update_sim_speed_text()

def enable_grid(event):
    global grid_on
    grid_on = not grid_on
    create_preview_square(event)
    if grid_on == True:
        canvas.itemconfigure('grid_line', state='normal')
        canvas.itemconfigure('square', width=1)
    else:
        canvas.itemconfigure('grid_line', state='hidden')
        canvas.itemconfigure('square', width=0)


def stop_time(event):
    global time_stop
    time_stop = not time_stop
    if time_stop == False:
        do_physics()

def delete_everything(event):
    canvas.delete('square')
    squares.clear()
    saved_positions.clear()

def do_physics():
    indexes_to_pop = []
    for idx, square in enumerate(squares):
        if is_position_valid(square[0], square[1] + pixel_radius): # check down
            canvas.move(square[2], 0, pixel_radius)
        else:
            right_down = False
            left_down = False
            if is_position_valid(square[0] + pixel_radius, square[1]) and is_position_valid(square[0] + pixel_radius, square[1] + pixel_radius): # check down-right
                right_down = True
            if is_position_valid(square[0] - pixel_radius, square[1]) and is_position_valid(square[0] - pixel_radius, square[1] + pixel_radius): # check down-left
                left_down = True

            if right_down == False and left_down == False:
                # The pixel cannot move down, down-left or down-right. To optimize rendering speeds, remove it from the squares list, and append its position to a
                # cached positions list, making the pixel "grounded" (cannot be moved no matter what)
                if is_position_grounded(square[0] + pixel_radius, square[1] + pixel_radius):
                    if is_position_grounded(square[0] - pixel_radius, square[1] + pixel_radius):
                        # if moving down-right & down-left is not possible, check if the squares are grounded (saved in saved_positions list) OR if the pixels are out of borders
                        indexes_to_pop.append(idx)
            elif right_down == True and left_down == True:
                # if both spaces are free, its 50/50 whether it goes left or right (fun factor)
                rng = random.randint(0, 1)
                # 0 = left, 1 = right
                if rng == 0: canvas.move(square[2], -pixel_radius, pixel_radius)
                else: canvas.move(square[2], pixel_radius, pixel_radius)

            elif right_down == True:
                canvas.move(square[2], pixel_radius, pixel_radius)
            elif left_down == True:
                canvas.move(square[2], -pixel_radius, pixel_radius)
        
        # update the square positions
        square[0] = round(canvas.coords(square[2])[0])
        square[1] = round(canvas.coords(square[2])[1])
    # END OF FOR LOOP:
    if len(indexes_to_pop) != 0:
        for index in indexes_to_pop:
            saved_positions.append(squares[index])
        for i, index in enumerate(indexes_to_pop):
            squares.pop(index - i)

    if time_stop == False:
        canvas.after(round(1 / target_fps * 1000), do_physics)

def stop_drawing(event):
    global is_drawing
    is_drawing = False

def start_drawing(event):
    global is_drawing
    is_drawing = True
    call_draw()

def call_draw():
    draw(event_var)
    if is_drawing == True:
        canvas.after(1, call_draw)

def measure_width_of_text(text: str, font_size: str) -> int:
    font = tkfont.Font(family = f'{font_family}', size = font_size, weight = 'normal')
    return font.measure(text)

def measure_height_of_text(text_size: int, text_font: str) -> int:
    font = tkfont.Font(family = f'{text_font}', size = text_size, weight = 'normal')
    return font.metrics("linespace")

def create_anchored_text(text: str, direction: str, line = 1, text_tag = 'anchored_text', font_size = font_size, color = 'black', fatness=''):
    '''
    directions: top_left, top, top_right, right, bottom_right, bottom, bottom_left, left
    directions other than top_left & top_right are bugged (too lazy to fix)
    '''
    x_center = WINDOW_WIDTH / 2
    y_center = WINDOW_HEIGHT / 2
    text_length = measure_width_of_text(text, font_size)
    text_height = measure_height_of_text(font_size, font_family)
    line_padding = text_height * (line - 1) + padding * line
    if direction == 'top_left':
        canvas.create_text(canvas.canvasx(0 + text_length / 2 + padding), 
                           canvas.canvasy(0 + text_height / 2 + line_padding), 
                           text = f'{text}', 
                           font = f'{font_family} {font_size} {fatness}',
                           tag = text_tag,
                           fill = color)
    elif direction == 'top':
        canvas.create_text(x_center, 
                           0 + text_height / 2 + line_padding,
                           text = f'{text}', 
                           font = f'{font_family} {font_size}',
                           tag = text_tag)
    elif direction == 'top_right':
        canvas.create_text(canvas.canvasx(WINDOW_WIDTH - text_length / 2 - padding - 10), 
                           canvas.canvasy(0 + text_height / 2 + line_padding), 
                           text = f'{text}', 
                           font = f'{font_family} {font_size} {fatness}',
                           tag = text_tag,
                           fill = color)
    elif direction == 'right':
        canvas.create_text(WINDOW_WIDTH - text_length / 2 - line_padding, 
                           y_center, 
                           text = f'{text}', 
                           font = f'{font_family} {font_size}',
                           tag = text_tag)
    elif direction == 'bottom_right':
        canvas.create_text(WINDOW_WIDTH - text_length / 2 - line_padding, 
                           WINDOW_HEIGHT - text_height / 2 - line_padding, 
                           text = f'{text}', 
                           font = f'{font_family} {font_size}',
                           tag = text_tag)
    elif direction == 'bottom':
        canvas.create_text(x_center, 
                           WINDOW_HEIGHT - text_height / 2 - line_padding, 
                           text = f'{text}', 
                           font = f'{font_family} {font_size}',
                           tag = text_tag)
    elif direction == 'bottom_left':
        canvas.create_text(0 + text_length / 2 + line_padding, 
                           WINDOW_HEIGHT - text_height / 2 - line_padding, 
                           text = f'{text}', 
                           font = f'{font_family} {font_size}',
                           tag = text_tag)
    elif direction == 'left':
        canvas.create_text(0 + text_length / 2 + line_padding, 
                           y_center, 
                           text = f'{text}', 
                           font = f'{font_family} {font_size}',
                           tag = text_tag)

def initialize_text():
    # NOTE: bad case of magic numbers in this function (and honestly, in a lot of other places too). Too bad!
    # TODO: make clearer in future project

    canvas.delete('anchored_text')
    create_anchored_text('CONTROLS:', 'top_left', 1.1, 'anchored_text', font_size, 'black', 'bold')
    create_anchored_text('CONTROLS:', 'top_left', 1, 'anchored_text', font_size, 'red', 'bold')

    create_anchored_text('H - Hide/show controls', 'top_left', 2.08, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('H - Hide/show controls', 'top_left', 2, 'anchored_text', font_size, 'black')

    create_anchored_text('X - Delete all sand', 'top_left', 3.08, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('X - Delete all sand', 'top_left', 3, 'anchored_text', font_size, 'black')

    create_anchored_text('T - Stop/continue simulation', 'top_left', 4.08, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('T - Stop/continue simulation', 'top_left', 4, 'anchored_text', font_size, 'black')

    create_anchored_text('G - Hide/show grid', 'top_left', 5.08, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('G - Hide/show grid', 'top_left', 5, 'anchored_text', font_size, 'black')

    create_anchored_text('SCROLL - Zoom in/out', 'top_left', 6.08, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('SCROLL - Zoom in/out', 'top_left', 6, 'anchored_text', font_size, 'black')

    create_anchored_text('DRAG MIDDLE MOUSE BUTTON (Mouse2) - Drag camera in mouse direction', 'top_left', 7.08, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('DRAG MIDDLE MOUSE BUTTON (Mouse2) - Drag camera in mouse direction', 'top_left', 7, 'anchored_text', font_size, 'black')

    create_anchored_text('(only possible if zoomed in)', 'top_left', 9.05, 'anchored_text', font_size - 3, 'HoneyDew')
    create_anchored_text('(only possible if zoomed in)', 'top_left', 9, 'anchored_text', font_size - 3, 'red')

    create_anchored_text('LEFT MOUSE BUTTON (Mouse1) - Draw sand', 'top_left', 8.55, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('LEFT MOUSE BUTTON (Mouse1) - Draw sand', 'top_left', 8.5, 'anchored_text', font_size, 'black')

    create_anchored_text('UP ARROW - Increase simulation Speed', 'top_left', 9.55, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('UP ARROW - Increase simulation Speed', 'top_left', 9.5, 'anchored_text', font_size, 'black')

    create_anchored_text('DOWN ARROW - Decrease simulation Speed', 'top_left', 10.55, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('DOWN ARROW - Decrease simulation Speed', 'top_left', 10.5, 'anchored_text', font_size, 'black')

    create_anchored_text('R - Reset simulation speed to 80 t/s', 'top_left', 11.55, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('R - Reset simulation speed to 80 t/s', 'top_left', 11.5, 'anchored_text', font_size, 'black')

    create_anchored_text('ESCAPE - Quit', 'top_left', 12.55, 'anchored_text', font_size, 'HoneyDew')
    create_anchored_text('ESCAPE - Quit', 'top_left', 12.5, 'anchored_text', font_size, 'black')

def show_help(event):
    global show_help_text
    show_help_text = not show_help_text
    if show_help_text == False:
        canvas.delete('anchored_text')
    else:
        initialize_text()

def on_closing(event):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

def increase_sim_speed(event):
    global target_fps
    target_fps += 1
    update_sim_speed_text()

def decrease_sim_speed(event):
    global target_fps
    if target_fps > 1:
        target_fps -= 1
    update_sim_speed_text()

def reset_sim_speed(event):
    global target_fps
    target_fps = 80
    update_sim_speed_text()

def update_sim_speed_text():
    canvas.delete('sim_speed')
    create_anchored_text(f'Simulation Speed: {target_fps} ticks/s', 'top_right', 1.08, 'sim_speed', font_size, 'HoneyDew', 'bold')
    create_anchored_text(f'Simulation Speed: {target_fps} ticks/s', 'top_right', 1, 'sim_speed', font_size, 'black', 'bold')

    create_anchored_text(f'Zoom level: {zoom_index}', 'top_right', 2.08, 'sim_speed', font_size, 'HoneyDew', 'bold')
    create_anchored_text(f'Zoom level: {zoom_index}', 'top_right', 2, 'sim_speed', font_size, 'black', 'bold')

initialize_text()
update_sim_speed_text()
do_physics()
center_screen()
create_grid_lines()

root.bind('<Escape>', on_closing)
root.bind('<MouseWheel>', zoom_in_or_out)
root.bind('<ButtonRelease-1>', stop_drawing)
root.bind('<Button-1>', start_drawing)
root.bind('<Motion>', create_preview_square)
root.bind('<Button-2>', scan_mark)
root.bind('<B2-Motion>', drag)
root.bind('<g>', enable_grid)
root.bind('<t>', stop_time)
root.bind('<x>', delete_everything)
root.bind('<h>', show_help)
root.bind('<Up>', increase_sim_speed)
root.bind('<Down>', decrease_sim_speed)
root.bind('<r>', reset_sim_speed)
root.mainloop()