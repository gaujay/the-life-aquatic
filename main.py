import math
import random
import tkinter as tk

# Project
from constants import *
import vectorutil as vu
from flora import Flora
from boid import Boid
from predator import Predator

def getNumberInput(message):
    num = int(input(message))
    return num

# Constants
#INI_PREDS = 4
INI_PREDS = getNumberInput("Enter the number of predators (1 - 100): ")
INI_BOIDS = getNumberInput("Enter the number of boids (1 - 25): ")
INI_FLORA = getNumberInput("Enter the number of flora (1 - 45): ")

BKGD_CLR = '#030A21'


# Init UI
master = tk.Tk()
master.title("The Life Aquatic")

canvas = tk.Canvas(master, bg=BKGD_CLR, width=CANVAS_W, height=CANVAS_H)
canvas.pack()

# Alias function
def _create_circle(self, x, y, r, **kwargs):
    return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)
tk.Canvas.create_circle = _create_circle


# Simulation functions
State = { 'iter': 0 }

#
def initSimulation():
    State['iter'] = 0

    for i in range(INI_FLORA):
        Flora(canvas)
        
    for i in range(INI_BOIDS):
        Boid(canvas)
    
    for i in range(INI_PREDS):
        Predator(canvas)
        
    Boid.setPredatorGrid(Predator.grid)

# 
def updateSimulation():
    # Update positions
    for boid in Boid.all:
        boid.updatePos()
        
    for pred in Predator.all:
        pred.updatePos()
    
    # Apply new positions
    for boid in Boid.all:
        boid.applyNewPos()
        
    for pred in Predator.all:
        pred.applyNewPos()
    
    # Update flora
    for flora in Flora.all:
        flora.updateGrowth()
    
    # Simulation end
    if len(Boid.all) == 0:
        print('Simulation iterations:', State['iter'])
        return
    
    # Simulation loop
    State['iter'] += 1
    master.after(1000//ITER_SEC, updateSimulation)

    
# Run simulation
initSimulation()
updateSimulation()

tk.mainloop()

