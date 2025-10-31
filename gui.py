# gui.py

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import os
import requests
import re
import threading
import sys
from queue import Queue, Empty
from ontology_reader import OntologyReader
from video_threads import HandTrackingThread, VideoCaptureThread
import base64
import google.generativeai as genai
import time

# --- YOU MUST REPLACE THIS WITH YOUR GEMINI API KEY ---
GEMINI_API_KEY = "<PLACE IN HERE>"
# --- YOU MUST REPLACE THIS WITH YOUR GEMINI API KEY ---

# Robobrain API Configuration
BASE_URL = "<PLACE IN HERE>" # REPLACE THIS WITH YOUR RoboBrain API
VERIFY_URL = f"{BASE_URL}verify"
PROMPT_URL = f"{BASE_URL}prompt"

# Terminal Output Switcher
class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.config(state=tk.NORMAL)

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

# Main GUI
class ApplianceControlGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Appliance Control (GUI, Ontology & Hand Tracking)")
        self.state('zoomed')
        
        self.ontology_reader = OntologyReader()
        self.selected_appliance_uri = None
        self.current_namespace = None
        self.current_appliance_id = None
        self.verified_image_id = None
        
        self.behaviour_sequence = []
        self.current_step = None
        self.step_queue = Queue()
        self.interaction_queue = Queue()

        self.frame_queue = Queue(maxsize=2)
        self.shutdown_event = threading.Event()
        
        # Droidcam or Camera
        self.camera_source = 0
        #self.camera_source = "<PLACE IN HERE>"  
        # REPLACE WITH YOUR DROIDCAM IP "http://<IP>:<PORT>"
        # REPLACE WITH "0" FOR DEVICE CAMERA (LAPTOP/PC)
        
        # Configure Gemini API
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        except Exception as e:
            messagebox.showerror("API Key Error", f"Failed to configure Gemini API. Check your API key. Error: {e}")
            self.destroy()
            return

        self.hand_thread = HandTrackingThread(self.frame_queue, self.shutdown_event)
        self.video_thread = VideoCaptureThread(
            self.camera_source, 
            self.interaction_queue, 
            self.frame_queue,
            self.hand_thread,
            self.shutdown_event
        )

        if not self.video_thread.cap.isOpened():
            messagebox.showerror("Error", "Unable to open webcam. Check camera connection.")
            self.destroy()
            return
            
        self.current_video_frame = None
        
        self.ontology_options = {
            "microwave": ("microwave_ontology.ttl", "http://www.example.org/microwave_ontology#", "microwave"),
            "kettle": ("ketel_ontology.ttl", "http://www.example.org/ketel_ontology#", "kettle"),
            "stove": ("stove_ontology.ttl", "http://www.example.org/stove_ontology#", "stove"),
            "laptop": ("laptop_ontology.ttl", "http://www.example.org/laptop_ontology#", "laptop")
            # UPLOAD YOUR ONTOLOGY URL 
            # "<OBJECT NAME>":("FILE NAME .ttl", "ONTOLOGY PREFIX IN YOUR ONTOLOGY FILE", "<OBJECT NAME IN YOUR ONTOLOGY>")
        }
        
        self.original_stdout = sys.stdout
        self.create_widgets()
        sys.stdout = StdoutRedirector(self.terminal_text)
        
        self.hand_thread.daemon = True 
        self.video_thread.daemon = True 
        
        self.video_thread.start()
        self.hand_thread.start()
        
        self.update_video_feed()
        self.check_interaction_queue()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('vista')
        style.configure("TFrame", background="#e0e0e0")
        style.configure("TLabel", background="#e0e0e0", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10, 'bold'))
        style.configure("TLabelFrame", font=('Arial', 12, 'bold'))
        
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(0, weight=0)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        top_container = ttk.Frame(main_frame)
        top_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        top_container.grid_columnconfigure(0, weight=1)
        top_container.grid_columnconfigure(1, weight=1)
        
        detection_frame = ttk.LabelFrame(top_container, text="Object Detection")
        detection_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ttk.Button(detection_frame, text="Detect Object", command=self.detect_object).pack(pady=10)
        self.detection_label = ttk.Label(detection_frame, text="Status: Waiting to detect...", font=('Arial', 10))
        self.detection_label.pack(pady=5)
        
        self.id_frame = ttk.LabelFrame(top_container, text="Appliance ID")
        self.id_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        id_info_frame = ttk.Frame(self.id_frame)
        id_info_frame.pack(pady=5)
        ttk.Label(id_info_frame, text="Appliance ID:").pack(side=tk.LEFT, padx=(0, 5))
        self.id_label = ttk.Label(id_info_frame, text="N/A", font=('Arial', 10, 'bold'))
        self.id_label.pack(side=tk.LEFT, padx=(0, 10))
        self.status_label = ttk.Label(id_info_frame, text="🔴", font=('Arial', 16))
        self.status_label.pack(side=tk.LEFT)
        ttk.Button(self.id_frame, text="Re-Verification", command=self.verify_appliance).pack(pady=5)

        mid_container = ttk.Frame(main_frame)
        mid_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        mid_container.grid_columnconfigure(0, weight=1)
        mid_container.grid_columnconfigure(1, weight=3)
        mid_container.grid_columnconfigure(2, weight=1)
        mid_container.grid_rowconfigure(0, weight=1)
        mid_container.grid_rowconfigure(1, weight=1)
        
        self.functions_frame = ttk.LabelFrame(mid_container, text="Available Functions (from Ontology)")
        self.functions_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        self.create_scrollable_frame(self.functions_frame, "functions")

        video_frame = ttk.LabelFrame(mid_container, text="Live Camera Feed")
        video_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        video_frame.grid_rowconfigure(0, weight=1)
        video_frame.grid_columnconfigure(0, weight=1)
        self.video_label = ttk.Label(video_frame)
        self.video_label.grid(row=0, column=0, sticky="nsew")
        
        self.behaviour_frame = ttk.LabelFrame(mid_container, text="Behaviour Controls")
        self.behaviour_frame.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=5, pady=5)
        self.create_scrollable_frame(self.behaviour_frame, "behaviour")

        terminal_frame = ttk.LabelFrame(mid_container, text="Terminal Output")
        terminal_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        terminal_frame.grid_rowconfigure(0, weight=1)
        terminal_frame.grid_columnconfigure(0, weight=1)
        self.terminal_text = tk.Text(terminal_frame, wrap="word", bg="#333", fg="#eee", insertbackground="white")
        self.terminal_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def create_scrollable_frame(self, parent_frame, name):
        canvas = tk.Canvas(parent_frame, bg="#f9f9f9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        inner_frame = ttk.Frame(canvas, style="TFrame")
        
        inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        if name == "functions":
            self.functions_inner_frame = inner_frame
        elif name == "behaviour":
            self.behaviour_inner_frame = inner_frame

    def check_interaction_queue(self):
        try:
            message = self.interaction_queue.get_nowait()
            if message == "TOUCH_DETECTED":
                print("🚀 Touch detected! Proceed to the next step.")
                if self.current_step:
                    self.behaviour_sequence.append(self.current_step)
                self.execute_next_step()
        except Empty:
            pass
        finally:
            self.after(100, self.check_interaction_queue)

    def detect_object(self):
        self.detection_label.config(text="Status: Detecting object...")
        print("Starting object detection...")
        
        frame = self.video_thread.get_frame()
        if frame is None:
            self.detection_label.config(text="Status: Failed to get frame.")
            print("Failed to get frame from video thread.")
            return

        threading.Thread(target=self._run_detection_thread, args=(frame,)).start()

    def _run_detection_thread(self, frame):
        try:
            # Convert frame to image format for Gemini
            _, buffer = cv2.imencode('.jpg', frame)
            base64_image = base64.b64encode(buffer).decode('utf-8')
            
            prompt = "What is the main object in this image? Respond with only a single word in lowercase."
            
            image_part = {
                "mime_type": "image/jpeg",
                "data": base64_image
            }

            response = self.gemini_model.generate_content([prompt, image_part])
            
            detected_object = response.text.strip().lower()
            
            self.after(0, self._handle_detection_result, detected_object)

        except Exception as e:
            self.after(0, self._handle_detection_error, e)
        

    def _handle_detection_result(self, detected_object):
        print(f"Gemini detected: '{detected_object}'")
        self.detection_label.config(text=f"Status: Detected '{detected_object}'")
        
        if detected_object in self.ontology_options:
            print(f"Found a matching ontology for '{detected_object}'. Loading file...")
            self.load_appliance_ontology(detected_object)
            self.after(200, self.verify_appliance)
        else:
            print(f"No ontology file found for '{detected_object}'.")
            self.detection_label.config(text=f"Status: No ontology found for '{detected_object}'")
            messagebox.showinfo("Ontology Not Found", f"No ontology file found for '{detected_object}'.")
            self.id_label.config(text=detected_object)
            self.status_label.config(text="🔴")
            
    def _handle_detection_error(self, e):
        print(f"❌ Error during Gemini API call: {e}")
        self.detection_label.config(text="Status: Detection failed.")
        messagebox.showerror("Gemini API Error", f"Failed to detect object. Check API key or network connection. Error: {e}")

    def load_appliance_ontology(self, selected_key):
        if not selected_key:
            return
        
        try:
            file, namespace_uri, appliance_id = self.ontology_options[selected_key]
            self.current_namespace = self.ontology_reader.load_ontology(file, namespace_uri)
            self.selected_appliance_uri = self.current_namespace[appliance_id]
            self.current_appliance_id = appliance_id
            self.id_label.config(text=appliance_id)
            self.verified_image_id = None
            self.status_label.config(text="🟡")
            
            self.behaviour_sequence = []
            self.step_queue = Queue()
            self.current_step = None
            
            first_step = self.ontology_reader.get_first_step(self.selected_appliance_uri, self.current_namespace)
            if first_step:
                self.step_queue.put(first_step)
            else:
                print("No steps were detected in the ontology.")
                
            self.update_behaviour_flowchart()
            self.update_functions_gui()
            print(f"Successfully switched to {appliance_id}.")
        except Exception as e:
            messagebox.showerror("Ontology Error", f"Failed to load ontology: {e}")
            
    def update_functions_gui(self):
        for widget in self.functions_inner_frame.winfo_children():
            widget.destroy()

        if self.selected_appliance_uri and self.current_namespace:
            functions = self.ontology_reader.get_appliance_functions(self.selected_appliance_uri, self.current_namespace)

            if not functions:
                ttk.Label(self.functions_inner_frame, text="No functions found.", foreground="#888").pack(pady=10)
                return

            for func in functions:
                func_name = func['name']
                func_mp = func['implements_mp']

                function_panel = ttk.Frame(self.functions_inner_frame, relief="groove", borderwidth=1, padding=5)
                function_panel.pack(fill="x", padx=5, pady=5)
                
                ttk.Label(function_panel, text=f"Function: {func_name}").pack(anchor="w", padx=5, pady=2, fill="x")
                ttk.Label(function_panel, text=f"MP: {func_mp}").pack(anchor="w", padx=5, pady=2, fill="x")
                
                ttk.Button(function_panel, text="Add to Queue", command=lambda f=func: self.add_function_to_queue(f)).pack(anchor="e", padx=5, pady=2)

    def add_function_to_queue(self, func_details):
        step = {
            "step_uri": None,
            "function_name": func_details['name'],
            "implements_mp": func_details['implements_mp'],
            "uri": func_details['uri']
        }
        self.step_queue.put(step)
        print(f"Function '{func_details['name']}' added to queue.")
        self.update_behaviour_flowchart()
        
        if self.current_step is None:
            self.execute_next_step()

    def verify_appliance(self):
        if not self.current_appliance_id:
            messagebox.showwarning("Warning", "Please detect an object first.")
            return
        
        print(f"Starting verification for {self.current_appliance_id}...")
        self.status_label.config(text="🟡")
        
        frame = self.video_thread.get_frame()
        if frame is None:
            print("Failed to get frame from video thread.")
            self.status_label.config(text="🔴")
            return
        
        threading.Thread(target=self._run_verification_thread, args=(frame,)).start()

    def _run_verification_thread(self, frame):
        try:
            temp_image_path = "temp_frame.jpg"
            cv2.imwrite(temp_image_path, frame)
            
            with open(temp_image_path, 'rb') as image_file:
                files = {'image': (os.path.basename(temp_image_path), image_file, 'image/jpeg')}
                payload = {'object_id': self.current_appliance_id}

                print(f"Sending verification request to Robobrain API for {self.current_appliance_id}...")
                response = requests.post(VERIFY_URL, files=files, data=payload, timeout=20)
                response.raise_for_status()
            
            result = response.json()
            verified_image_id = result.get("image_id")
            
            self.after(0, self._handle_verification_result, verified_image_id)
        except requests.exceptions.RequestException as e:
            self.after(0, self._handle_verification_error, e)
        finally:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

    def _handle_verification_result(self, verified_image_id):
        self.verified_image_id = verified_image_id
        if self.verified_image_id:
            print(f"✅ Verification successful! Image ID: {self.verified_image_id}")
            self.status_label.config(text="🟢")
            
            if not self.step_queue.empty():
                print("Starting ontology steps...")
                self.execute_next_step()
            else:
                messagebox.showinfo("Ontology Sequence", "Verification was successful, but no sequence of steps was found.")
        else:
            print("❌ Verification was successful, but image_id was not found in the response.")
            self.status_label.config(text="🔴")
            messagebox.showerror("Verification Error", "Verification was successful but no image ID was returned.")
    
    def _handle_verification_error(self, e):
        print(f"❌ Error communicating with Robobrain API: {e}")
        self.status_label.config(text="🔴")
        messagebox.showerror("Network Error", f"Unable to connect to Robobrain server: {e}")

    def get_coordinates_from_roborain(self, prompt):
        if not self.verified_image_id:
            messagebox.showwarning("Warning", "Device not verified.")
            return None
        
        try:
            payload = {'image_id': self.verified_image_id, 'prompt': prompt}
            print(f"Sending prompt to Robobrain API: '{prompt}' with Image ID: {self.verified_image_id}...")
            response = requests.post(PROMPT_URL, data=payload, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            answer_text = result.get('answer', '')
            print(f"Response from Robobrain: {answer_text}")

            point_pattern = r'\(\s*(\d+)\s*,\s*(\d+)\s*\)'
            extracted_points = re.findall(point_pattern, answer_text)
            
            if extracted_points:
                return [(int(x), int(y)) for x, y in extracted_points]
            else:
                print("RoboBrain did not find the coordinates.")
                return []
        except requests.exceptions.RequestException as e:
            print(f"❌ Error communicating with Robobrain API: {e}")
            messagebox.showerror("Network Error", f"Unable to connect to Robobrain server: {e}")
            return None

    def execute_next_step(self):
        if not self.step_queue.empty():
            if self.current_step:
                self.behaviour_sequence.append(self.current_step)

            self.current_step = self.step_queue.get()
            print(f"\n▶️ Execute steps: {self.current_step['function_name']}")
            self.update_behaviour_flowchart()
            
            threading.Thread(target=self._run_execute_function_thread, args=(self.current_step,)).start()
        else:
            if self.current_step:
                self.behaviour_sequence.append(self.current_step)
            self.current_step = None
            print("The ontology sequence is complete.")
            self.update_behaviour_flowchart()

    def _run_execute_function_thread(self, step_details):
        func_name = step_details['function_name']
        prompt = f"show me the location of the '{func_name}'."
        coordinates = self.get_coordinates_from_roborain(prompt)

        if coordinates is not None:
            self.after(0, self._handle_function_result, step_details, coordinates)
            
    def _handle_function_result(self, step_details, coordinates):
        if coordinates:
            print(f"Successfully obtained coordinates from Robobrain: {coordinates}")
            
            frame = self.video_thread.get_frame()
            if frame is not None:
                self.video_thread.create_trackers(coordinates, frame)
        else:
            print("Robobrain did not find coordinates for this command.")
            messagebox.showinfo("Target Not Found", f"Robobrain did not find a target for '{step_details['function_name']}'.")
        
        if step_details.get('step_uri'):
            next_step = self.ontology_reader.get_next_step(step_details['step_uri'], self.current_namespace)
            if next_step:
                self.step_queue.put(next_step)
        
        if not coordinates:
            self.execute_next_step()
            
    def update_behaviour_flowchart(self):
        for widget in self.behaviour_inner_frame.winfo_children():
            widget.destroy()

        all_steps = self.behaviour_sequence + ([self.current_step] if self.current_step else [])
        
        if not all_steps:
            ttk.Label(self.behaviour_inner_frame, text="The order will appear here.", foreground="#888").pack(pady=10)
            return

        for i, step in enumerate(all_steps):
            is_current = self.current_step and step.get("function_name") == self.current_step.get("function_name")
            
            step_frame = ttk.Frame(self.behaviour_inner_frame, relief="solid", borderwidth=1, padding=10)
            step_frame.pack(fill="x", padx=10, pady=5)
            
            if is_current:
                style = ttk.Style()
                style.configure("Current.TFrame", background="#d0e0ff")
                step_frame.config(style="Current.TFrame")
            else:
                step_frame.config(style="TFrame")
                
            ttk.Label(step_frame, text=f"{i+1}. {step['function_name']}", font=('Arial', 10, 'bold')).pack(anchor="w")
            ttk.Label(step_frame, text=f"MP: {step['implements_mp']}", font=('Arial', 9)).pack(anchor="w")
            
            if is_current:
                ttk.Label(step_frame, text="Waiting for interaction...", font=('Arial', 9, 'italic'), foreground="blue").pack(anchor="w")

            if i < len(all_steps) - 1:
                arrow_label = ttk.Label(self.behaviour_inner_frame, text="▼", font=('Arial', 16), foreground="#888")
                arrow_label.pack(pady=2)

    def update_video_feed(self):
        frame = self.video_thread.get_frame()

        if frame is not None:
            h, w, _ = frame.shape
            max_w, max_h = 854, 480
            ratio = min(max_w / w, max_h / h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            
            img_resized = cv2.resize(frame, (new_w, new_h))
            img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            
            self.current_video_frame = ImageTk.PhotoImage(image=img_pil)
            self.video_label.config(image=self.current_video_frame)
            self.video_label.image = self.current_video_frame

        self.after(30, self.update_video_feed)
    
    def on_closing(self):
        print("Closing application. Signaling threads to stop...")
        self.shutdown_event.set()
        
        if self.hand_thread and self.hand_thread.is_alive():
            print("Waiting for hand tracking thread to join...")
            self.hand_thread.join(timeout=2)
        if self.video_thread and self.video_thread.is_alive():
            print("Waiting for video capture thread to join...")
            self.video_thread.join(timeout=2)
        
        print("All threads have been stopped. Destroying GUI.")
        sys.stdout = self.original_stdout
        self.destroy()