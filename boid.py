import random
import numpy as np
# Project
from constants import *
import vectorutil as vu
from flora import *

# Constants
BOID_H = 17
BOID_W = BOID_H*2/3
BOID_HH = BOID_H/2
BOID_HW = BOID_W/2
BOID_CLR = ['#128ECF', '#1DAAE7', '#0760F3']


class Boid:
    """A Class representing boid elements.
    Capable of moving as flocks, eating flora and reproducing.
    They are the food source of predators, which they try to avoid.
    """
    
    # Constants
    maxForce = 0.05 * 60/ITER_SEC
    maxRoamSpeed = 3.5 * 60/ITER_SEC
    maxEscapeSpeed = 4.5 * 60/ITER_SEC
    inertiaRatio = 0.33
    
    gestationTime = 9*ITER_SEC
    fertileThld = 3*ITER_SEC
    matingChance = 0.5
    ttlPregnant = 0
    reproMax = 35
    
    hungerRate = 80./ITER_SEC
    hungerMax = 1500.
    hungerThld = hungerMax/3.
    floraNrgRatio = 0.75
    
    # Static
    all = []
    grid = []
    predatorGrid = None # Externally set
    
    # Init static
    for i in range(GRID_W):
        grid.append( [] )
        for j in range(GRID_H):
            grid[i].append( [] )
    
    #
    @staticmethod
    def setPredatorGrid(predGrid):
        Boid.predatorGrid = predGrid
    
    #
    def removeFromGrid(self):
        Boid.grid[int(self.pos[0] // VISION_RAD)][int(self.pos[1] // VISION_RAD)].remove(self)
    
    #
    def updateGrid(self, remove=True):
        if remove:
            # Only if cell changed
            if (  int(self.pos[0] // VISION_RAD) == int(self.nxt[0] // VISION_RAD)
              and int(self.pos[1] // VISION_RAD) == int(self.nxt[1] // VISION_RAD) ):
                return
            Boid.grid[int(self.pos[0] // VISION_RAD)][int(self.pos[1] // VISION_RAD)].remove(self)
        # Add
        Boid.grid[int(self.nxt[0] // VISION_RAD)][int(self.nxt[1] // VISION_RAD)].append(self)
    
    #
    def getNearCells(self):
        return vu.getNearCellsFromPos(self.pos, VISION_RAD, GRID_W-1, GRID_H-1)
    
    #
    def distanceSqr(self, other):
        return vu.distanceSqrWrapped(self.pos, other.pos)
    
    #
    #
    def __init__(self, canvas, pos=None, isNewborn=False):
        if pos is not None:
            self.pos = pos
        else:
            self.pos = np.array([ random.randint(0, CANVAS_W-1),
                                  random.randint(0, CANVAS_H-1) ])
        self.nxt = self.pos
        
        self.vel = vu.randomUnitVector()
        self.vel *= random.uniform(2., Boid.maxRoamSpeed)
        self.vxt = self.vel
        self.maxSpeed = Boid.maxRoamSpeed
        
        self.acc = np.array([0., 0.])
        self.inertiaRatio = Boid.inertiaRatio
        
        self.gender = random.choice('MF')
        if self.gender == 'M':
            if isNewborn: self.fertile = 0
            else: self.fertile = random.randint(0, Boid.fertileThld)
        else:
            self.gestation = 0
        
        self.hunger = random.randint(0, Boid.hungerThld)
        self.eating = None
        self.caught = False
        
        self.updateGrid(False)
        self.points = vu.updateTriPoints(self.nxt, self.vel, BOID_HH, BOID_HW)

        self.canvas = canvas
        self.id = self.canvas.create_polygon(self.points, fill=random.choice(BOID_CLR))
        
        Boid.all.append(self)
    

    #
    def align(self):
        steer = np.array([0., 0.])
        sum   = np.array([0., 0.])
        nbr = 0
        
        cells = self.getNearCells()
        for cell in cells:
            for boid in Boid.grid[cell[0]][cell[1]]:
                if boid is not self and boid.eating is None and self.distanceSqr(boid) <= VISION_RADSQR:
                    sum += boid.vel
                    nbr += 1
        # Apply
        if nbr > 0:
            steer = sum / nbr
            steer = vu.setMag(steer, Boid.maxRoamSpeed)
            steer -= self.vel
            steer = vu.capMag(steer, Boid.maxForce)
            
        return steer
    
    #
    def cohesion(self):
        steer = np.array([0., 0.])
        sum = np.array([0., 0.])
        nbr = 0
        
        cells = self.getNearCells()
        for cell in cells:
            for boid in Boid.grid[cell[0]][cell[1]]:
                if boid is not self and boid.eating is None and self.distanceSqr(boid) <= VISION_RADSQR:
                    sum += vu.wrapRelativePos(self.pos, boid.pos)
                    nbr += 1
        # Apply
        if nbr > 0:
            steer = sum / nbr
            steer -= self.pos
            steer = vu.setMag(steer, Boid.maxRoamSpeed)
            steer -= self.vel
            steer = vu.capMag(steer, Boid.maxForce)
            
        return steer
        
     #
    def separation(self):
        steer = np.array([0., 0.])
        sum = np.array([0., 0.])
        nbr = 0
        
        cells = self.getNearCells()
        for cell in cells:
            for boid in Boid.grid[cell[0]][cell[1]]:
                sqrDist = self.distanceSqr(boid)
                if boid is not self and boid.eating is None and sqrDist <= VISION_RADSQR*0.5:
                    if sqrDist < EPSILON: sqrDist = EPSILON
                    diff = self.pos - vu.wrapRelativePos(self.pos, boid.pos)
                    sum += vu.setMag(diff, 1./sqrDist)
                    nbr += 1
        # Apply
        if nbr > 0:
            steer = sum / nbr
            steer = vu.setMag(steer, Boid.maxRoamSpeed)
            steer -= self.vel
            steer = vu.capMag(steer, Boid.maxForce)
            
        return steer
    
    #
    def roam(self):
        self.hunger += Boid.hungerRate
        # Flocking (with arbitrary weight)
        steer = self.align()*1.1
        steer += self.cohesion()*0.9
        steer += self.separation()*1.
        steer = vu.capMag(steer, Boid.maxForce*2.)
        
        return steer
    
    #
    def mating(self):
        if (self.gender == 'F' or len(Boid.all) + Boid.ttlPregnant >= Boid.reproMax
            or self.hunger >= Boid.hungerThld or self.fertile < Boid.fertileThld):
            return
    
        cells = self.getNearCells()
        for cell in cells:
            for boid in Boid.grid[cell[0]][cell[1]]:
                if boid is not self and boid.gender == 'F' and boid.gestation <= 0:
                    success = random.uniform(0., 1.) <= Boid.matingChance
                    if success:
                        # if DEBUG_LOG: print('Pregnant boid:', self.id)
                        boid.gestation = 1
                        Boid.ttlPregnant += 1
                    self.fertile = 0 # cool down
                    return
    
    # 
    def getBiggestClosestFlora(self):
        res = None
        maxSize = -1
        minSqrDist = -1.
        
        cells = Flora.getNearCells(self.pos)
        for cell in cells:
            for flora in Flora.grid[cell[0]][cell[1]]:
                sqrDist = self.distanceSqr(flora)
                if sqrDist <= FLORA_RADSQR:
                    if (res is None or flora.val > maxSize
                      or (flora.val == maxSize and sqrDist < minSqrDist)):
                        res = flora
                        maxSize = flora.val
                        minSqrDist = sqrDist
    
        return res
    
    #
    def managePredators(self):
        escaping = False
        sum = np.array([0., 0.])
        nbr = 0
    
        cells = self.getNearCells()
        for cell in cells:
            for pred in Boid.predatorGrid[cell[0]][cell[1]]:
                sqrDist = self.distanceSqr(pred)
                if sqrDist <= VISION_RADSQR:
                    diff = self.pos - vu.wrapRelativePos(self.pos, pred.pos)
                    sum += vu.setMag(diff, 1./sqrDist)
                    nbr += 1
        # Apply
        if nbr > 0:
            steer = sum / nbr
            steer = vu.setMag(steer, Boid.maxEscapeSpeed)
            steer -= self.vel
            steer = vu.setMag(steer, Boid.maxForce*8.)
            self.acc = steer
            
            self.hunger += Boid.hungerRate
            escaping = True
    
        return escaping
    
    #
    def manageReproduction(self):
        if self.gender == 'M':
            if self.fertile < Boid.fertileThld:
                self.fertile += 1
        else:
            if self.gestation > 0:
                self.gestation += 1
                if self.gestation >= Boid.gestationTime:
                    Boid(self.canvas, vu.getAdjacentPos(self.pos, BOID_H*2), True)
                    self.gestation = 0
                    Boid.ttlPregnant -= 1
                    if DEBUG_LOG:
                        print('Newborn boid:', self.id)
                        if len(Boid.all) == Boid.reproMax: print('>> MAX BOIDS!')
    
    #
    def killed(self):
        self.canvas.delete(self.id)
        if self.gender == 'F' and self.gestation > 0:
            Boid.ttlPregnant -= 1
        self.removeFromGrid()
        Boid.all.remove(self)
        if DEBUG_LOG:
            if len(Boid.all) == 0: print('>> NO MORE BOIDS!')
    
    #
    def starved(self):
        starved = self.hunger >= Boid.hungerMax
        if starved:
            if DEBUG_LOG: print('Starved boid:', self.id)
            self.killed()
            
        return starved
    
    #
    def manageHunger(self):
        hungry = (self.hunger >= Boid.hungerThld
            or (self.eating is not None and self.hunger > 0)) # Or eating but not full
    
        if hungry:
            bite = -1.
            if self.eating is not None: bite = self.eating.takeBite()
            
            # Still eating (immobile)
            if bite > 0.:
                self.hunger -= bite * Boid.floraNrgRatio
                self.acc *= 0.
                self.vxt *= 0.
            # Look for flora
            else:
                self.eating = None
                
                closestFlora = self.getBiggestClosestFlora()
                if closestFlora is None: # Keep looking
                    self.acc += self.roam() 
                else:
                    sqrDist = self.distanceSqr(closestFlora)
                    nearDist = max(BOID_HH**2, closestFlora.rad**2)
                    # Close enough to eat
                    if sqrDist <= nearDist:
                        bite = closestFlora.takeBite()
                        if bite > 0.:
                            self.hunger -= bite * Boid.floraNrgRatio
                            self.eating = closestFlora
                            self.acc *= 0.
                            self.vxt *= 0.
                    # Go toward flora
                    else:
                        self.hunger += Boid.hungerRate

                        steer = vu.wrapRelativePos(self.pos, closestFlora.pos) - self.pos
                        steer = vu.setMag(steer, Boid.maxRoamSpeed)
                        steer -= self.vel
                        steer = vu.capMag(steer, Boid.maxForce*2)
                        self.acc = steer
        
        return hungry
    
    
    #    
    def updatePos(self):
        # Update state
        self.acc *= self.inertiaRatio
        
        # Reproduction
        self.manageReproduction()
        
        # Show stoppers
        if self.caught or self.starved():
            return
        
        # Escape predator
        escaping = self.managePredators()
        
        if not escaping:
            self.maxSpeed = Boid.maxRoamSpeed
            
            # Hungry
            hungry = self.manageHunger()
            
            # Roam free
            if not hungry:
                self.eating = None
                self.mating()
                self.acc += self.roam()
        else:
            self.eating = None
            self.maxSpeed = Boid.maxEscapeSpeed
        
        # Special case: immobile -> random push
        if self.eating is None and vu.norm(self.acc) < EPSILON and vu.norm(self.vxt) < EPSILON:
            self.acc = vu.randomUnitVector() * Boid.maxForce
            # if DEBUG_LOG: print('Random push:', self.id)
        # No deceleration if not at full speed
        if vu.norm(self.vxt) < self.maxSpeed:
            self.inertiaRatio = 1.
        else:
            self.inertiaRatio = Boid.inertiaRatio
        
        # Apply acceleration
        self.acc = vu.capMag(self.acc, Boid.maxForce*8.) # Saturate acc
        self.vxt += self.acc
        self.vxt = vu.capMag(self.vxt, self.maxSpeed)  # Saturate vel
        self.nxt = np.add(self.nxt, self.vxt)
        
        # Update position + rotation
        if ((self.acc[0] != 0. or self.acc[1] != 0.)
            and (self.vxt[0] != 0. or self.vxt[1] != 0)):
            # Warp around
            vu.wrapEdges(self)
        
            self.points = vu.updateTriPoints(self.nxt, self.vel, BOID_HH, BOID_HW)
        # Update position only
        else:
            # Move
            self.points = [ self.points[0]+self.vxt[0], self.points[1]+self.vxt[1],
                            self.points[2]+self.vxt[0], self.points[3]+self.vxt[1],
                            self.points[4]+self.vxt[0], self.points[5]+self.vxt[1] ]
            # Warp around
            vu.wrapEdges(self, True)
        
        # Apply
        if ( self.pos[0] != self.nxt[0] or self.pos[1] != self.nxt[1]
          or self.vel[0] != self.vxt[0] or self.vel[1] != self.vxt[1] ):
            self.canvas.coords(self.id, *self.points)
            self.canvas.update_idletasks()
        
    #
    def applyNewPos(self):
        self.updateGrid()
        self.pos = self.nxt
        self.vel = self.vxt

