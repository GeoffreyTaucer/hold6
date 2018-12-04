import tkinter
from tkinter import ttk
import cv2 as cv
import PIL.Image
import PIL.ImageTk
import detector


class App:
    def __init__(self, root, window_title, video_source=0):
        self.root = root
        self.root.title(window_title)
        self.detecting = False
        self.image = None
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

        self.checkbox_ding = ttk.Checkbutton(self.control_frame, text="Ding for successful hold", state="disabled")
        self.checkbox_ding.grid(row=1, column=0, sticky="W")

        self.checkbox_video_out = ttk.Checkbutton(self.control_frame, text="Output video", state="disabled")
        self.checkbox_video_out.grid(row=2, column=0, sticky="W")

        self.button_detect = ttk.Button(self.control_frame, text="Start detection", command=self.detector_switch)
        self.button_detect.grid(row=3, column=0, sticky="W")

        self.button_calibrate = ttk.Button(self.control_frame, text="Calibrate", state="disabled")
        self.button_calibrate.grid(row=4, column=0, sticky="W")

        self.button_exit = ttk.Button(self.control_frame, text="Exit program", command=exit)
        self.button_exit.grid(row=5, column=0, sticky="W")

        self.label_status = ttk.Label(self.control_frame, text="")
        self.label_status.grid(row=6, column=0, sticky="W")

        self.delay = 16
        self.update_video()

        self.root.mainloop()

    def detector_switch(self):
        self.detecting = not self.detecting
        if self.detecting:
            self.button_detect.configure(text="Stop detection")

        else:
            self.button_detect.configure(text="Start detection")

    def update_video(self):
        frame = self.vid.get_frame()
        if frame is None:
            self.detecting = False
            return

        self.image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))

        # if self.detecting:
        #
        #     if not 0 < self.non_ref_frames <= 3:
        #         self.ref_frame = self.image
        #
        #     if self.is_hold(self.image, self.ref_frame):
        #         self.hold_frames += 1

        self.display_canvas.create_image(0, 0, image=self.image, anchor="nw")

        self.root.after(self.delay, self.update_video)


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
