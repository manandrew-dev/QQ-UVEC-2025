# Description
Our project takes a python file and analyzes the code to see if it could be more modular and maintainable. Furthermore, our project returns a suggestion on how the user could modularize their code. Our implementation of this project uses McCabe's complexity topics and Maintainability Index metrics to measure how many independent execution paths exists in the program and estimates how easy the code is to maintain.

# Implementation
To first analyze the Python code that the user inputs, we first analyze each part of the file. From the imports/importfroms to classes to functions, we dissect each part using an AST structure. Afterwards, our program uses Radon to calculate the McCabe Complexity measure how independant paths are in the program. Along side McCabe Complexity, we are also using the Maintainability Index to compute how maintainable the code truly is. Moving on from the mathematical analysis, we then use diffib to find any functions that might be near duplicated or duplicates. Reaching close to the end, we then make a map of the dependencies to see which moddules are related to each other. Finally the code returns readable suggestions to better improve the user's code writing skills. 

## Required packages (Action Needed)
```bash
pip install radon
```
Used to caluate and compute our McCabe Complexity and Maintainability Index.
The rest of the libraries are built into Python.

```bash
pip install uvicorn

pip install fastapi
```
Required to run the FastAPI server.

```bash
npm install
```
Since we are using React to help with our frontend, you will need to install the necessary packages from react before being able to run the local server.

## How-to-Run
### Backend
```bash
uvicorn main:app --reload
```
Run the backend first.
### Frontend
```bash
npm run dev
```
While the backend is running, then run the frontend.

# Features
- Simple accessible User Interface
- Interative code edititor 
- File selector

#  Usage
For Computer Science Stuednts and other STEM majors who are passionite in improving their coding skills by seeing if their code could be more readable and maintainable. 

# Visuals
PowerPoint:
https://docs.google.com/presentation/d/1zGjqu_ROewuvgvQIqkuzQDLwv9vJp5iutJjwOAQ7Zg8/edit?usp=sharing

# Problem relevance, limitations, and Roadmap
## Problem Relevance
Students, beginner Python developers, and open-source contributers all have one thing in common. They struggle to recall or identify what they had written as the code becomes more and more complex. With our code, users are able to measure maintainability and modularity encouraging for better coding practices and readability. 

## Limitations
- Our current model only analyzes one file at a time.
- Suggestions are rule-based instead of being context based.
- Results are text based, and does not support graphical charts.

## Roadmap
- Support multiple files for analysis
- context based suggestions instead of being rule-based
- Educational feedback, explaining why certain scores are high or low

