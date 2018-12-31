import tkinter
from tkinter import ttk
import cv2 as cv
import PIL.Image
import PIL.ImageTk
from time import time
from playsound import playsound
from threading import Thread


# noinspection PyBroadException
class App:
    def __init__(self, root, window_title, video_source=0):
        self.root = root
        self.root.title(window_title)
        self.detecting = False
        self.image = None
        self.trigger = 500
        self.hold_goal = 0
        self.hold_start = 0
        self.hold_time = 0
        self.hold_frames = 0
        self.no_hold_frames = 0
        self.holding = 0
        self.ding_enabled = tkinter.IntVar()
        self.played_ding = False

        self.video_source = video_source

        self.vid = VideoCapture(video_source)
        self.f1 = cv.cvtColor(self.vid.get_frame(), cv.COLOR_BGR2GRAY)
        self.f2 = cv.cvtColor(self.vid.get_frame(), cv.COLOR_BGR2GRAY)
        self.f3 = cv.cvtColor(self.vid.get_frame(), cv.COLOR_BGR2GRAY)

        self.display_frame = ttk.Frame(self.root, borderwidth=2, relief="groove")
        self.display_frame.grid(row=0, column=1)
        self.display_canvas = tkinter.Canvas(self.display_frame, width=self.vid.in_width, height=self.vid.in_height)
        self.display_canvas.pack()

        self.control_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.control_frame.grid(row=0, column=0, sticky="nw")

        self.goal_frame = ttk.Frame(self.control_frame)
        self.goal_frame.grid(column=0, row=0, sticky="W")
        self.label_hold_goal = ttk.Label(self.goal_frame, text="Hold goal: ")
        self.input_goal = ttk.Entry(self.goal_frame, width=5)
        self.label_seconds = ttk.Label(self.goal_frame, text=" seconds")
        self.label_hold_goal.grid(column=0, row=0, sticky="W")
        self.input_goal.grid(column=1, row=0, sticky="E")
        self.label_seconds.grid(column=2, row=0, sticky="W")

        self.checkbox_ding = ttk.Checkbutton(self.control_frame, text="Ding for successful hold",
                                             variable=self.ding_enabled)
        self.checkbox_ding.grid(row=1, column=0, sticky="W")

        # self.checkbox_video_out = ttk.Checkbutton(self.control_frame, text="Output video", state="disabled")
        # self.checkbox_video_out.grid(row=2, column=0, sticky="W")

        self.button_detect = ttk.Button(self.control_frame, text="Start detection", command=self.detector_switch)
        self.button_detect.grid(row=3, column=0, sticky="W")

        self.button_calibrate = ttk.Button(self.control_frame, text="Calibrate", state="disabled")
        self.button_calibrate.grid(row=4, column=0, sticky="W")

        self.button_exit = ttk.Button(self.control_frame, text="Exit program", command=exit)
        self.button_exit.grid(row=5, column=0, sticky="W")

        self.label_status_1 = ttk.Label(self.control_frame, text="")
        self.label_status_1.grid(row=6, column=0, sticky="W")

        self.label_status_2 = ttk.Label(self.control_frame, text="")
        self.label_status_2.grid(row=7, column=0, sticky="W")

        self.label_hold_time = tkinter.Label(self.control_frame, text="", font=("", 96))
        self.label_hold_time.grid(row=7, column=0)

        self.delay = 16
        self.update_video()

        self.root.mainloop()

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
            self.reset()

    def reset(self):
        self.hold_start = 0
        self.hold_time = 0
        self.hold_frames = 0
        self.no_hold_frames = 0
        self.holding = 0
        self.played_ding = False

    def update_video(self):
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

        self.display_canvas.create_image(0, 0, image=self.image, anchor="nw")

        self.root.after(self.delay, self.update_video)

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

        if self.hold_frames == 10:
            self.no_hold_frames = 0
            self.holding = True

        elif self.no_hold_frames == 5:
            self.hold_frames = 0
            self.holding = False

        if self.holding and not self.hold_start:
            self.hold_start = time()

        elif self.holding and self.hold_start:
            self.hold_time = time() - self.hold_start
            self.hold_time = round(self.hold_time, 1)
            if self.hold_time >= self.hold_goal and self.ding_enabled.get():
                self.playding()

            color = "red"

            if self.hold_time > self.hold_goal:
                color = "green"

            self.label_hold_time.configure(text=str(self.hold_time), fg=color)

        elif not self.holding and self.hold_time:
            self.reset()

    def is_hold(self):
        total_diff = self.get_total_diff()
        self.label_status_1.configure(text=str(total_diff))
        return total_diff < self.trigger

    def get_total_diff(self):
        d1 = cv.absdiff(self.f3, self.f2)
        d2 = cv.absdiff(self.f2, self.f3)
        bit_and = cv.bitwise_and(d1, d2)
        _, thresh_bin = cv.threshold(bit_and, 32, 255, cv.THRESH_BINARY)
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
