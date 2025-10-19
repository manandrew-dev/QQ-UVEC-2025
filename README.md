### Description
Our project takes a python file and analyzes the code to see if it could be more modular and maintainable. Furthermore, our project retruns a suggestion on how the user could modularize their code. Our implementation of this project uses McCabe's complexity topics and Maintainability Index metrics to measure how many independent execution paths exists in the program and estimates how easy the code is to maintain.

### Implementation
To first analyze the Python code that the user inputs, we first analyze each part of the file. From the imports/importfroms to classes to functions, we dissect each part using an AST structure. Afterwards, our program uses Radon to calculate the McCabe Complexity measure how independant paths are in the program. Along side McCabe Complexity, we are also using the Maintainability Index to compute how maintainable the code truly is. Moving on from the mathematical analysis, we then use diffib to find any functions that might be near duplicated or duplicates. Reaching close to the end, we then make a map of the dependencies to see which moddules are related to each other. Finally the code returns readable suggestions to better improve the user's code writing skills. 

## Required packages (Action Needed)
"""bash
pip install radon
"""
Used to caluate and compute our McCabe Complexity and Maintainability Index.
The rest of the libraries are built into Python.