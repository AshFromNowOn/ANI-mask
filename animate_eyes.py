from evdev import InputDevice, ecodes
from PIL import Image, ImageOps
import ST7789
import time
import sys
import os


class eyeController:

    def __init__(self, control_device="event3", eye_dir="eyes"):

        self.img_dimensions = (240, 240)

        self.axis_range = (0, 255)

        
        self.eye_r = ST7789.ST7789(
            height=240,
            rotation=90,
            port=0,
            cs=ST7789.BG_SPI_CS_FRONT,
            dc=9,
            backlight=19,
            spi_speed_hz=40 * 1000 * 1000,
            offset_left=40,
            offset_top=0
        )
        self.eye_l = ST7789.ST7789(
            height=240,
            rotation=90,
            port=0,
            cs=ST7789.BG_SPI_CS_BACK,
            dc=9,
            backlight=18,
            spi_speed_hz=40 * 1000 * 1000,
            offset_left=40,
            offset_top=0
        )

        self.eye_l.begin()
        self.eye_r.begin()



        self.eye_images = {}
        for file in os.listdir(eye_dir):
            filename = os.fsdecode(file)
            if filename.endswith(".png") or filename.endswith(".gif"):
                print(filename)
                self.eye_images[filename] = Image.open(os.path.join(eye_dir, filename))
        
        # print(self.eye_images.keys())

        self.button_to_eye_map = {  # left eye img, right eye img, True if flip one of the eyes for mirror effect
            "":     (self.eye_images['eye_open.png'], self.eye_images['eye_open.png'], True), 
            "u":    (self.eye_images['eye_happy.png'], self.eye_images['eye_happy.png'], True),
            "d":    (self.eye_images['eye_frustrate_closed.png'], self.eye_images['eye_frustrate_closed.png'], True),
            "l":    (self.eye_images['eye_question.png'], self.eye_images['eye_question.png'], False),
            "r":    (self.eye_images['eye_exclaim.png'], self.eye_images['eye_exclaim.png'], True),
            "ld":   (self.eye_images['eye_heart.png'], self.eye_images['eye_heart.png'], True)
            # "lu":
            # "lr":
            # "du":
            # "dr":
            "ur":   (self.eye_images['eye_frustrate_closed.png'], self.eye_images['eye_open.png'], True),
            # "ldu":
            # "ldr":
            # "lur":
            # "dur": 
            "ldur": (self.eye_images['eye_loading.png'], self.eye_images['eye_loading.png'], False)
        }

        self.get_eye_images("ldur")
        print("Connecting to Bluetooth Controller")
        # self.controller = InputDevice("/dev/input/{}".format(control_device))
        self.connect_to_controller(control_device)

    def get_buttons(self):
        keys = self.controller.active_keys()
        button_map_key = ""
        # if not keys:
        #     return button_map_key
        for key in keys:
            if key == 304:
                button_map_key += "l"
            if key == 305:
                button_map_key += "d"
            if key == 307:
                button_map_key += "u"
            if key == 308:
                button_map_key += "r"

        return button_map_key

    def get_joystick(self):
        x_axis = self.controller.absinfo(ecodes.ABS_X).value
        y_axis = self.controller.absinfo(ecodes.ABS_Y).value
        # print("X: {}".format(x_axis))
        # print("Y: {}".format(y_axis))
        return (y_axis, x_axis)

    def get_eye_images(self, buttons=""):
        # buttons = self.get_buttons()

        try:
            l_img, r_img, flip = self.button_to_eye_map[buttons]
        except KeyError:
            l_img, r_img, flip = self.button_to_eye_map[""]

        if flip:
            l_img = ImageOps.mirror(l_img)

        # print(l_img.size)

        if l_img.size > self.img_dimensions or r_img.size > self.img_dimensions:
            # open eye. Enable lookaround
           l_img = self.get_cropped_image(l_img)
           r_img = self.get_cropped_image(r_img)


        self.eye_l.display(l_img)
        self.eye_r.display(r_img)

    def connect_to_controller(self, control_device):
        connected = False
        while not connected:
            try:
                self.controller = InputDevice("/dev/input/{}".format(control_device))
                connected = True
            except (FileNotFoundError, PermissionError):
                print("No Controller found, retrying connection")
                time.sleep(1)

        print(self.controller)
        print(self.controller.capabilities(verbose=True))
        print(self.controller.leds(verbose=True))

    def get_cropped_image(self, img):
        
        img_centre = (img.size[0] / 2, img.size[1] / 2)
        top_corner = (img_centre[0]-(self.img_dimensions[0]/2), img_centre[1]-(self.img_dimensions[1]/2))
        # crop_square = (top_corner[0], top_corner[1], top_corner[0]+self.img_dimensions[0], top_corner[1]+self.img_dimensions[1])
        joystick_vals = self.get_joystick()

        
        x_adjust = self.maprange(self.axis_range, (0, top_corner[0]), joystick_vals[0]) - top_corner[0]/2
        y_adjust = self.maprange(self.axis_range, (0, top_corner[1]), joystick_vals[1]) - top_corner[1]/2

        crop_square = (top_corner[0] - x_adjust, top_corner[1] - y_adjust, top_corner[0]+self.img_dimensions[0] - x_adjust, top_corner[1]+self.img_dimensions[1] - y_adjust)
        
        return img.crop(crop_square)


    def maprange(self, a, b, s):
        (a1, a2), (b1, b2) = a, b
        return  b1 + ((s - a1) * (b2 - b1) / (a2 - a1))
        




if __name__ == "__main__":
    if sys.argv[1]:
        controller = eyeController(eye_dir=sys.argv[1])
    else:
        controller = eyeController()
    while True:
        controller.get_joystick()
        controller.get_eye_images(controller.get_buttons())
