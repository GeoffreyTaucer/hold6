import tkinter
from tkinter import ttk
import cv2 as cv
import PIL.Image
import PIL.ImageTk
from time import time
from playsound import playsound
from threading import Thread
import sys


# noinspection PyBroadException
class App:
    def __init__(self, root, window_title, video_source=0):
        self.root = root
        self.root.title(window_title)
        self.detecting = False
        self.image = None
        self.move_thresh = 32
        self.area_thresh = 150
        self.hold_goal = 0
        self.hold_start = 0
        self.hold_time = 0
        self.hold_frames = 0
        self.no_hold_frames = 0
        self.holding = 0
        self.ding_enabled = tkinter.IntVar()
        self.played_ding = False
        self.calibrating = False
        self.has_calibrated = False
        self.total_diff = 0

        self.video_source = video_source

        self.vid = VideoCapture(video_source)
        self.f1 = cv.cvtColor(self.vid.get_frame(), cv.COLOR_BGR2GRAY)
        self.f2 = cv.cvtColor(self.vid.get_frame(), cv.COLOR_BGR2GRAY)
        self.f3 = cv.cvtColor(self.vid.get_frame(), cv.COLOR_BGR2GRAY)

        self.display_frame = ttk.Frame(self.root, borderwidth=2, relief="groove")
        self.display_frame.grid(row=0, column=1, rowspan=2)
        self.display_canvas = tkinter.Canvas(self.display_frame, width=self.vid.in_width, height=self.vid.in_height)
        self.display_canvas.pack()

        self.control_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.control_frame.grid(row=0, column=0, sticky="nw")
        self.exit_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.exit_frame.grid(row=1, column=0, sticky="SW")

        # main widgets
        self.goal_frame = ttk.Frame(self.control_frame)
        self.label_hold_goal = ttk.Label(self.goal_frame, text="Hold goal: ")
        self.input_goal = ttk.Entry(self.goal_frame, width=5)
        self.label_seconds = ttk.Label(self.goal_frame, text=" seconds")
        self.checkbox_ding = ttk.Checkbutton(self.control_frame, text="Ding for successful hold",
                                             variable=self.ding_enabled)
        # self.checkbox_video_out = ttk.Checkbutton(self.control_frame, text="Output video", state="disabled")
        self.button_detect = ttk.Button(self.control_frame, text="Start detection", command=self.detector_switch)
        self.button_calibrate = ttk.Button(self.control_frame, text="Calibrate",
                                           command=self.calibrate_switch)
        # self.button_calibrate.bind("<Enter>", lambda _: self.show_info("Not yet implemented"))
        # self.button_calibrate.bind("<Leave>", lambda _: self.show_info(""))
        self.button_exit = ttk.Button(self.exit_frame, text="Exit program", command=sys.exit)
        self.label_info = ttk.Label(self.control_frame, text="", wraplength=145)
        self.label_holding = ttk.Label(self.control_frame, text="")
        self.label_hold_time = tkinter.Label(self.control_frame, text="", font=("", 96))
        self.main_widgets = [self.goal_frame, self.label_hold_goal, self.input_goal, self.label_seconds,
                             self.checkbox_ding, self.button_detect, self.button_calibrate]

        # calibration widgets
        self.movement_thresh_frame = ttk.Frame(self.control_frame, padding="10 10 10 10")
        self.label_movement_thresh = ttk.Label(self.movement_thresh_frame, text="Motion thresh")
        self.input_movement_thresh = ttk.Entry(self.movement_thresh_frame, width=4)
        self.move_thresh_infotext = "Should be between 0 and 255. This determines the threshold for what counts as " \
                                    "movement. Look for the lowest value where Total Difference stays at 0 when " \
                                    "there is no movement. Default value is 32"
        self.movement_thresh_frame.bind("<Enter>", lambda _: self.show_info(self.move_thresh_infotext))
        self.movement_thresh_frame.bind("<Leave>", lambda _: self.show_info(""))

        self.area_thresh_frame = ttk.Frame(self.control_frame, padding="10 10 10 10")
        self.label_area_thresh = ttk.Label(self.area_thresh_frame, text="Area thresh")
        self.input_area_thresh = ttk.Entry(self.area_thresh_frame, width=8)
        self.area_thresh_infotext = "This determines how much movement is acceptable without breaking the hold, " \
                                    "and can be used to ignore small movements. Total Difference should be below " \
                                    "this number while the athlete is still, and above this number while the " \
                                    "athlete is moving. Default value is 150."
        self.area_thresh_frame.bind("<Enter>", lambda _: self.show_info(self.area_thresh_infotext))
        self.area_thresh_frame.bind("<Leave>", lambda _: self.show_info(""))

        self.button_apply_vals = ttk.Button(self.control_frame, text="Apply", command=self.apply_cal_vals)

        self.label_total_diff = ttk.Label(self.control_frame, text=f"Total Difference: {self.get_total_diff()}")

        self.button_exit_calibration = ttk.Button(self.control_frame, text="Return",
                                                  command=self.calibrate_switch)

        self.calibration_widgets = [self.movement_thresh_frame, self.label_movement_thresh, self.input_movement_thresh,
                                    self.area_thresh_frame, self.label_area_thresh, self.input_area_thresh,
                                    self.label_total_diff, self.button_apply_vals, self.button_exit_calibration]

        self.label_info.grid(row=5, column=0, sticky="W")
        self.button_exit.grid(row=0, column=0, sticky="SW")

        self.grid_main()

        self.delay = 16
        self.update()

        self.root.mainloop()

    def show_info(self, text):
        self.label_info.configure(text=text)

    def grid_main(self):
        if self.has_calibrated:
            for widget in self.calibration_widgets:
                widget.grid_forget()

        # grid main widgets
        self.goal_frame.grid(column=0, row=0, sticky="W")
        self.label_hold_goal.grid(column=0, row=0, sticky="W")
        self.input_goal.grid(column=1, row=0, sticky="E")
        self.label_seconds.grid(column=2, row=0, sticky="W")
        self.checkbox_ding.grid(row=1, column=0, sticky="W")
        # self.checkbox_video_out.grid(row=2, column=0, sticky="W")
        self.button_detect.grid(row=3, column=0, sticky="W")
        self.button_calibrate.grid(row=4, column=0, sticky="W")
        self.label_hold_time.grid(row=6, column=0)

    def grid_calibrate(self):
        for widget in self.main_widgets:
            widget.grid_forget()

        # add code here to grid calibration widgets
        self.movement_thresh_frame.grid(column=0, row=0, sticky="W")
        self.label_movement_thresh.grid(column=0, row=0, sticky="W")
        self.input_movement_thresh.grid(column=1, row=0, sticky="E")

        self.area_thresh_frame.grid(column=0, row=1, sticky="W")
        self.label_area_thresh.grid(column=0, row=0, sticky="W")
        self.input_area_thresh.grid(column=1, row=0, sticky="E")

        self.button_apply_vals.grid(column=0, row=2)

        self.label_total_diff.grid(column=0, row=3)

        self.button_exit_calibration.grid(column=0, row=4, sticky="W")

    def apply_cal_vals(self):
        self.move_thresh = tkinter.IntVar()
        self.area_thresh = tkinter.IntVar()

        try:
            self.move_thresh = int(self.input_movement_thresh.get())

        except Exception:
            self.move_thresh = 32

        if self.move_thresh < 0 or self.move_thresh > 255:
            self.move_thresh = 32

        try:
            self.area_thresh = int(self.input_area_thresh.get())

        except Exception:
            self.area_thresh = 200

        if self.area_thresh < 0:
            self.area_thresh = 200

    def calibrate_switch(self):
        if self.calibrating:
            self.grid_main()

        else:
            self.grid_calibrate()

        self.calibrating = not self.calibrating
        self.has_calibrated = True

    def set_hold_goal(self):
        try:
            self.hold_goal = int(self.input_goal.get())

        except Exception:
            self.hold_goal = 0

    def detector_switch(self):
        self.detecting = not self.detecting
        if self.detecting:
            self.set_hold_goal()
            self.button_detect.configure(text="Stop detection")

        else:
            self.button_detect.configure(text="Start detection")
            self.label_holding.configure(text="")
            self.label_hold_time.configure(text="")
            self.reset()

    def reset(self):
        self.hold_start = 0
        self.hold_time = 0
        self.hold_frames = 0
        self.no_hold_frames = 0
        self.holding = 0
        self.played_ding = False

    def update(self):
        frame = self.vid.get_frame()
        if frame is None:
            self.detecting = False
            return

        self.f1 = self.f2
        self.f2 = self.f3
        self.f3 = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        self.image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))

        if self.detecting:
            self.detector_main()

        if self.calibrating:
            self.label_total_diff.configure(text=f"Total difference: {self.get_total_diff()}")

        self.display_canvas.create_image(0, 0, image=self.image, anchor="nw")

        self.root.after(self.delay, self.update)

    def playding(self):
        if not self.played_ding:
            Thread(target=playsound, args=("ding.mp3",)).start()
        self.played_ding = True

    def detector_main(self):
        hold = self.is_hold()

        if hold:
            self.hold_frames += 1

        else:
            self.no_hold_frames += 1

        if self.hold_frames == 15:
            self.no_hold_frames = 0
            self.holding = True
            self.label_holding.configure(text="Holding")

        elif self.no_hold_frames == 3:
            self.hold_frames = 0
            self.holding = False
            self.label_holding.configure(text="")

        if self.holding and not self.hold_start:
            self.hold_start = time()

        elif self.holding and self.hold_start:
            self.hold_time = time() - self.hold_start
            self.hold_time = round(self.hold_time, 1)

            if self.hold_time >= self.hold_goal and self.ding_enabled.get():
                self.playding()

            color = "red"

            if self.hold_time >= self.hold_goal:
                color = "green"

            self.label_hold_time.configure(text=str(self.hold_time), fg=color)

        elif not self.holding and self.hold_time:
            self.reset()

    def is_hold(self):
        return self.get_total_diff() < self.area_thresh

    def get_total_diff(self):
        d1 = cv.absdiff(self.f1, self.f2)
        d2 = cv.absdiff(self.f2, self.f3)
        bit_and = cv.bitwise_and(d1, d2)
        _, thresh_bin = cv.threshold(bit_and, self.move_thresh, 255, cv.THRESH_BINARY)
        # cv.imshow("Test", thresh_bin)
        return cv.countNonZero(thresh_bin)

    def add_overlay(self):
        pass


class VideoCapture:
    def __init__(self, video_source=0):
        self.vid = cv.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video", video_source)

        self.in_width = self.vid.get(cv.CAP_PROP_FRAME_WIDTH)
        self.in_height = self.vid.get(cv.CAP_PROP_FRAME_HEIGHT)

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

    def get_frame(self):
        is_frame, frame = self.vid.read()

        if is_frame:
            return cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        return None


if __name__ == '__main__':
    App(tkinter.Tk(), "Hold Detector")
