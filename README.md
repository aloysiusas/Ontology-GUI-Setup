# Ontology-GUI-Setup

Ontology-GUI setup
Git clone the repository to your device with the following link: https://github.com/aloysiusas/Ontology-GUI-Setup 
Install all required libraries
pip install Pillow
manipulating images, especially to display video feeds from OpenCV into Tkinter
pip install opencv-python
processing video from the camera
pip install requests
send an HTTP request to the Robobrain API
pip install google-generativeai
interact with the Gemini API
pip install rdflib
to read and process ontology files
pip install mediapipe
Google's MediaPipe library for hand tracking


How to Run the Program
Make sure your project directory and files are structured as shown above.
Open your terminal or command prompt.
Navigate to the file directory.
Run the program using the command: python main.py
How to use?
Run the program. 
The GUI display will appear as shown in the image. 

Then, press the “Detect object” button to verify the object using the Gemini API. If it is not recognised, press the button again.




The object is considered verified when the “Appliance ID” displays the object name and the “Available functions” display appears on the left.

The system will automatically execute the first step by displaying the process in the “Behaviour Controls” section.







After the system successfully executes the first step, the coordinates will appear on the screen. 

Display your hand in the camera area so that hand tracking can work. When your hand touches the coordinates, the system will automatically continue executing the second step. Perform these steps until completion.


