# Ontology-GUI-Setup

**Ontology-GUI setup**
1. Git clone the repository to your device with the following link: https://github.com/aloysiusas/Ontology-GUI-Setup 
2. Install all required libraries with “pip install ...”
- Pillow
- opencv-python
- requests
- google-generativeai
- rdflib
- mediapipe

**How to Run the Program**
1. Make sure your project directory and files are structured as shown above.
2. Open your terminal or command prompt.
3. Navigate to the file directory.
4. Run the program using the command: python main.py

**How to use?**
1. Run the program. 
2. The GUI display will appear as shown in the image.
<p align="center"> 
  <img src=how_to_use/GUI_Display.png alt=GUI_display width="600">
</p>

3. Then, press the “Detect object” button to verify the object using the Gemini API. If it is not recognised, press the button again.
<p align="center"> 
  <img src=how_to_use/Detect_object.png alt=Detect_object width="600">
</p>

4. The object is considered verified when the “Appliance ID” displays the object name and the “Available functions” display appears on the left.
<p align="center"> 
  <img src=how_to_use/Verified_object.png alt=Verified_object width="600">
</p>

5. The system will automatically execute the first step by displaying the process in the “Behaviour Controls” section.
<p align="center"> 
  <img src=how_to_use/System_running.png alt=System_running width="600">
</p>
6. After the system successfully executes the first step, the coordinates will appear on the screen.
<p align="center"> 
  <img src=how_to_use/Coordinate.png alt=Coordinate width="600">
</p>
7. Display your hand in the camera area so that hand tracking can work. When your hand touches the coordinates, the system will automatically continue executing the second step. Perform these steps until completion. 
<p align="center"> 
  <img src=how_to_use/Hand_tracking.png alt=Hand_tracking width="600">
</p>
<p align="center"> 
  <img src=how_to_use/Hand_tracking_done.png alt=Hand_tracking_done width="600">
</p>
