import math
import random
import numpy as np
# Project
from constants import *
import vectorutil as vu

# Constants
FLORA_RAD = 100
FLORA_RADSQR = FLORA_RAD**2
FLORA_GRID_W = math.ceil(CANVAS_W / FLORA_RAD)
FLORA_GRID_H = math.ceil(CANVAS_H / FLORA_RAD)
FLORA_CLR = ['#00AD85', '#07866D']


class Flora:
    """A Class representing flora elements.
    Capable of growing and reproducing, they are the food source of boids.
    """
    
    # Constants
    growthRate = 50./ITER_SEC
    maxVal = 1000.
    biteRate = 600./ITER_SEC
    
    repro1Ratio = 0.5
    reproNRatio = 1.
    reproMax = 70
    reproRandPos = 0.2
    
    # Static
    all = []
    grid = []
    
    # Init static
    for i in range(FLORA_GRID_W):
        grid.append( [] )
        for j in range(FLORA_GRID_H):
            grid[i].append( [] )

    #
    @staticmethod
    def getNearCells(pos):
        return vu.getNearCellsFromPos(pos, FLORA_RAD, FLORA_GRID_W-1, FLORA_GRID_H-1)
    
    #
    def addToGrid(self):
        Flora.grid[int(self.pos[0]) // FLORA_RAD][int(self.pos[1]) // FLORA_RAD].append(self)
        
    #
    def removeFromGrid(self):
        Flora.grid[int(self.pos[0]) // FLORA_RAD][int(self.pos[1]) // FLORA_RAD].remove(self)
    
    #
    #
    def __init__(self, canvas, pos=None):
        if pos is not None:
            self.pos = pos
            self.val = random.randint(Flora.maxVal*0.1, Flora.maxVal*0.2)
        else:
            self.pos = np.array([ random.randint(0, CANVAS_W-1),
                                  random.randint(0, CANVAS_H-1) ])
            self.val = random.randint(Flora.maxVal*0.2, Flora.maxVal*0.67)
            
        self.rad = int(self.val / 100.) + 1
        self.repro = False
        self.rpCtr = 0

        self.addToGrid()
        
        self.canvas = canvas
        self.id = self.canvas.create_circle(self.pos[0], self.pos[1],
                                             self.rad, fill=random.choice(FLORA_CLR))
        self.canvas.tag_lower(self.id)
        
        Flora.all.append(self)
        
    
    #
    def takeBite(self):
        res = Flora.biteRate
    
        if self.val < Flora.biteRate:
            res = self.val
            self.val = -1.
        else:
            self.val -= Flora.biteRate
            
        return res
    
    #
    def updateGrowth(self):
        # Alive
        if self.val > 0.:
            # Grow
            if self.val < Flora.maxVal:
                self.val += Flora.growthRate
                if self.val > Flora.maxVal: self.val = Flora.maxVal
                prevRad = self.rad
                self.rad = int(self.val / 100.) + 1
                
                # Apply
                if self.rad != prevRad:
                    points = [ self.pos[0]-self.rad, self.pos[1]-self.rad,
                               self.pos[0]+self.rad, self.pos[1]+self.rad ]
                    self.canvas.coords(self.id, *points)
                    self.canvas.update_idletasks()

            # Reproduce
            if len(Flora.all) >= Flora.reproMax:    # Limit
                self.rpCtr = 0  # Wasted
                return
            
            if self.repro:
                self.rpCtr += Flora.growthRate
                # if self.rpCtr >= Flora.maxVal*Flora.reproNRatio:
                    # if DEBUG_LOG: print('Seed reset:', self.id)
            
            if ( (not self.repro and self.val >= Flora.maxVal*Flora.repro1Ratio)
                   or self.rpCtr >= Flora.maxVal*Flora.reproNRatio ):
                # if DEBUG_LOG: print('Seed:', self.id)
                pos = vu.getAdjacentPos(self.pos, Flora.maxVal*2.5/100.,
                                        Flora.maxVal*5./100., Flora.reproRandPos)
                Flora(self.canvas, pos)
                self.canvas.tag_lower(self.id) # Stay below child
                self.repro = True
                self.rpCtr = 0
                # if DEBUG_LOG and len(Flora.all) == Flora.reproMax:
                    # print('>> MAX FLORA!')
            
        # Eaten
        else:
            # if DEBUG_LOG: print('Eaten:', self.id)
            self.canvas.delete(self.id)
            self.removeFromGrid()
            Flora.all.remove(self)
            if len(Flora.all) == 0:
                if DEBUG_LOG: print('>> NO MORE FLORA!')

