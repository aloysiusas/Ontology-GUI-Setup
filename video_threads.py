# video_threads.py

import threading
import cv2
import mediapipe as mp
import math
from queue import Queue, Empty

# Initialize MediaPipe solutions
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

class HandTrackingThread(threading.Thread):
    def __init__(self, frame_queue, shutdown_event):
        super().__init__()
        self.frame_queue = frame_queue
        self.latest_results = None
        self.results_lock = threading.Lock() 
        self.shutdown_event = shutdown_event
        self.hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)

    def run(self):
        print("Hand tracking thread starts.")
        while not self.shutdown_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=0.05)
                if frame is None:
                    continue
                
                imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(imgRGB)

                with self.results_lock:
                    self.latest_results = results

            except Empty:
                continue
            except Exception as e:
                print(f"Error in HandTrackingThread: {e}")
        
        self.hands.close()
        print("Hand tracking thread stopped.")

    def get_results(self):
        with self.results_lock:
            return self.latest_results

class VideoCaptureThread(threading.Thread):
    def __init__(self, camera_source, interaction_queue, frame_queue, hand_tracking_thread, shutdown_event):
        super().__init__()
        self.camera_source = camera_source
        self.interaction_queue = interaction_queue
        self.frame_queue = frame_queue
        self.hand_thread = hand_tracking_thread
        self.shutdown_event = shutdown_event
        
        self.frame = None
        self.frame_lock = threading.Lock()
        self.tracker_lock = threading.Lock()

        self.trackers = []
        self.dot_radius = 10
        self.dot_color = (0, 0, 255)
        self.touch_radius = 10
        
        # New attributes for historical smoothing
        self.thumb_tip_history = []
        self.index_tip_history = []
        self.history_size = 5  # Number of past frames to average
        
        self.cap = cv2.VideoCapture(self.camera_source)
    
    def run(self):
        if not self.cap.isOpened():
            print("Error: Could not open video stream.")
            self.shutdown_event.set()
            return
        
        print("Video capture thread started.")
        while not self.shutdown_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                print("Video stream ended, releasing camera.")
                break
            
            #frame = cv2.flip(frame, 1)

            if not self.frame_queue.full():
                self.frame_queue.put_nowait(frame.copy())

            results = self.hand_thread.get_results()

            tracker_centers = []
            with self.tracker_lock:
                self._update_trackers(frame)
                
                for tracker in self.trackers:
                    success, bbox = tracker.update(frame) 
                    if success:
                        center_x = int(bbox[0] + bbox[2] / 2)
                        center_y = int(bbox[1] + bbox[3] / 2)
                        tracker_centers.append((center_x, center_y))

            if results and results.multi_hand_landmarks:
                for handLms in results.multi_hand_landmarks:
                    # Draw landmarks on the frame
                    mp_drawing.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
                    
                    thumb_tip = handLms.landmark[4]
                    index_tip = handLms.landmark[8]
                    
                    h, w, c = frame.shape
                    
                    # Get the raw finger point coordinates
                    thumb_point_raw = (int(thumb_tip.x * w), int(thumb_tip.y * h))
                    index_point_raw = (int(index_tip.x * w), int(index_tip.y * h))
                    
                    # Apply smoothing by updating history
                    smoothed_thumb_point = self._update_history(self.thumb_tip_history, thumb_point_raw)
                    smoothed_index_point = self._update_history(self.index_tip_history, index_point_raw)

                    # Use the smoothed points for distance calculation
                    finger_points = [smoothed_thumb_point, smoothed_index_point]

                    for dot_center in tracker_centers:
                        for finger_tip in finger_points:
                            distance = math.dist(dot_center, finger_tip)
                            if distance < self.touch_radius:
                                self.interaction_queue.put("TOUCH_DETECTED")
                                with self.tracker_lock:
                                    self.trackers = []
                                break
                        else: continue
                        break
            
            with self.frame_lock:
                self.frame = frame
        
        if self.cap:
            self.cap.release()
        print("The video capture thread stops.")

    def get_frame(self):
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None
            
    def _update_trackers(self, frame): 
        updated_trackers = []
        if not self.trackers:
            return
        
        for tracker in self.trackers:
            success, bbox = tracker.update(frame)
            if success:
                center_x = int(bbox[0] + bbox[2] / 2)
                center_y = int(bbox[1] + bbox[3] / 2)
                cv2.circle(frame, (center_x, center_y), self.dot_radius, self.dot_color, -1)
                updated_trackers.append(tracker)
            else:
                print("Tracking failed for one point.")
        self.trackers = updated_trackers

    def create_trackers(self, points, frame):
        new_trackers = []
        for point in points:
            x, y = point
            bbox = (max(0, x - 50), max(0, y - 50), 100, 100) 
            
            tracker = cv2.TrackerKCF_create()
            try:
                tracker.init(frame, bbox)
                new_trackers.append(tracker)
            except Exception as e:
                print(f"Failed to initialize tracker: {e}")
        
        with self.tracker_lock:
            self.trackers = new_trackers

    # New method to manage the historical data and calculate the average for smoothing.
    def _update_history(self, history, new_point):
        """Adds a new point to the history and returns the smoothed average."""
        history.append(new_point)
        
        # Keep the history list at a fixed size by removing the oldest element if it's too long
        if len(history) > self.history_size:
            history.pop(0)
        
        # Calculate the average of all points in the history
        avg_x = sum(p[0] for p in history) / len(history)
        avg_y = sum(p[1] for p in history) / len(history)
        
        return (int(avg_x), int(avg_y))