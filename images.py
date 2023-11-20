import os
import pygame
import threading
import time

# Global variables
window_size = (1396, 785)
talking = True
reading = True
lock = threading.Lock()

def toggle_talking():
    with lock:
        global talking
        if not talking:
            time.sleep(0.3)
        talking = not talking

def toggle_reading():
    with lock:
        global reading
        reading = not reading

def display_images():
    global talking
    global reading
    # Set the path to the folder containing images
    image_folder = os.path.join(os.path.dirname(__file__), 'minion_pics')

    # Set the duration to display each image in milliseconds
    display_duration = 90

    # Initialize pygame
    pygame.init()

    # Create a window
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption('Minion Display')

    # Load all images into a list
    image_names = [f"minion_otto_talking_{i}.png" for i in range(1, 6)]
    images = [pygame.image.load(os.path.join(image_folder, name)) for name in image_names]
    gaming_image = pygame.image.load(os.path.join(image_folder, 'minion_otto_gaming.png'))
    reading_image = pygame.image.load(os.path.join(image_folder, 'chat_reading.png'))

    # Set the initial image index
    image_index = 0

    # Run the display loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Clear the screen
        screen.fill((255, 255, 255))

        # Display the appropriate image
        with lock:
            if reading:
                current_image = reading_image
            else:
                current_image = images[image_index] if talking else gaming_image

        # Blit the current image onto the screen
        screen.blit(current_image, (0, 0))

        # Update the display
        pygame.display.flip()

        # Increment the image index for the next iteration
        image_index = (image_index + 1) % len(images)

        # Wait for the specified duration
        pygame.time.delay(display_duration)

    # Quit pygame
    pygame.quit()

def start_display_thread():
    display_thread = threading.Thread(target=display_images)
    display_thread.start()
