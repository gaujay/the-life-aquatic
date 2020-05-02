import random
import numpy as np
# Project
from constants import *
import vectorutil as vu
from boid import Boid

# Constants
PRED_H = 25
PRED_W = PRED_H*2/3
PRED_HH = PRED_H/2
PRED_HW = PRED_W/2
PRED_CLR = '#BE2E3D'


class Predator:
    """A Class representing predator elements.
    Capable of roaming randomly, hunting boids and reproducing.
    """
    
    # Constants
    maxForce = 0.125 * 60/ITER_SEC
    maxRoamSpeed = 2.5 * 60/ITER_SEC
    maxHungrySpeed = 3 * 60/ITER_SEC
    maxHuntSpeed = 5.5 * 60/ITER_SEC
    inertiaRatio = 0.33
    roamDirChange = 3*ITER_SEC
    
    gestationTime = 9*ITER_SEC
    fertileThld = 3*ITER_SEC
    matingChance = 0.67
    ttlPregnant = 0
    reproMax = 6
    
    hungerRate = 85./ITER_SEC
    hungerMax = 1500.
    hungerThld = hungerMax/3.
    
    eatDuration = 2*ITER_SEC
    nrgPerBoid = 1000
    
    # Static
    all = []
    grid = []
    
    # Init static
    for i in range(GRID_W):
        grid.append( [] )
        for j in range(GRID_H):
            grid[i].append( [] )
    
    #
    @staticmethod
    def getMinorityGender():
        ttlMale = 0
        for pred in Predator.all:
            if pred.gender == 'M': ttlMale
        if ttlMale >= math.ceil(len(Predator.all) / 2):
            return 'F'
        return 'M'
    
    #
    def removeFromGrid(self):
        Predator.grid[int(self.pos[0] // VISION_RAD)][int(self.pos[1] // VISION_RAD)].remove(self)
    
    #
    def updateGrid(self, remove=True):
        if remove:
            if (  int(self.pos[0] // VISION_RAD) == int(self.nxt[0] // VISION_RAD)
              and int(self.pos[1] // VISION_RAD) == int(self.nxt[1] // VISION_RAD) ):
                return
            Predator.grid[int(self.pos[0] // VISION_RAD)][int(self.pos[1] // VISION_RAD)].remove(self)
        Predator.grid[int(self.nxt[0] // VISION_RAD)][int(self.nxt[1] // VISION_RAD)].append(self)

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
        self.vel *= random.uniform(1.5, Predator.maxRoamSpeed)
        self.vxt = self.vel
        self.maxSpeed = Predator.maxRoamSpeed
        
        self.acc = np.array([0., 0.])
        self.inertiaRatio = Predator.inertiaRatio
        self.roamCounter = 0
        
        self.gender = Predator.getMinorityGender() #random.choice('MF')
        if self.gender == 'M':
            if isNewborn: self.fertile = 0
            else: self.fertile = random.randint(0, Boid.fertileThld)
        else:
            self.gestation = 0
        
        self.hunger = random.randint(0, Predator.hungerThld/2.)
        self.eatCounter = 0
        self.eating = None
        
        self.updateGrid(False)
        self.points = vu.updateTriPoints(self.nxt, self.vel, PRED_HH, PRED_HW)

        self.canvas = canvas
        self.id = self.canvas.create_polygon(self.points, fill=PRED_CLR)
        self.canvas.tag_raise(self.id)
        
        Predator.all.append(self)


    #
    def roam(self):
        self.hunger += Predator.hungerRate
        steer = np.array([0., 0.])
        
        self.roamCounter +=1
        if self.roamCounter >= Predator.roamDirChange:
            steer = vu.randomUnitVector() * Predator.maxForce
            self.roamCounter = 0
        
        return steer
    
    #
    def getNearCells(self):
        return vu.getNearCellsFromPos(self.pos, VISION_RAD, GRID_W-1, GRID_H-1)
    
    #
    def mating(self):
        if (self.gender == 'F' or len(Predator.all) + Predator.ttlPregnant >= Predator.reproMax
            or self.hunger >= Predator.hungerThld or self.fertile < Predator.fertileThld):
            return
    
        cells = self.getNearCells()
        for cell in cells:
            for pred in Predator.grid[cell[0]][cell[1]]:
                if pred is not self and pred.gender == 'F' and pred.gestation <= 0:
                    success = random.uniform(0., 1.) <= Predator.matingChance
                    if success:
                        if DEBUG_LOG: print('Pregnant pred:', self.id)
                        pred.gestation = 1
                        Predator.ttlPregnant += 1
                    self.fertile = 0 # cool down
                    return
    
    #
    def manageReproduction(self):
        if self.gender == 'M':
            if self.fertile < Predator.fertileThld:
                self.fertile += 1
        else:
            if self.gestation > 0:
                self.gestation += 1
                if self.gestation >= Boid.gestationTime:
                    Predator(self.canvas, vu.getAdjacentPos(self.pos, PRED_H*2), True)
                    self.gestation = 0
                    Predator.ttlPregnant -= 1
                    if DEBUG_LOG:
                        print('Newborn pred:', self.id)
                        if len(Predator.all) == Predator.reproMax: print('>> MAX PREDATORS!')
    
    # 
    def getClosestBoid(self):
        res = None
        minSqrDist = -1.
        
        cells = self.getNearCells()
        for cell in cells:
            for boid in Boid.grid[cell[0]][cell[1]]:
                if not boid.caught:
                    sqrDist = boid.distanceSqr(self)
                    if sqrDist <= VISION_RADSQR:
                        if res is None or sqrDist < minSqrDist:
                            res = boid
                            minSqrDist = sqrDist
    
        return res
    
    #
    def starved(self):
        starved = self.hunger >= Predator.hungerMax
        if starved:
            self.canvas.delete(self.id)
            if self.gender == 'F' and self.gestation > 0:
                Predator.ttlPregnant -= 1
            self.removeFromGrid()
            Predator.all.remove(self)
            if DEBUG_LOG:
                print('Dead predator:', self.id)
                if len(Predator.all) == 0: print('>> NO MORE PREDATORS!')
            
        return starved
    
    #
    def manageHunger(self):
        hungry = (self.hunger >= Predator.hungerThld
            or (self.eating is not None and self.hunger > Predator.hungerRate)) # Or eating but not full
    
        self.maxSpeed = Predator.maxRoamSpeed
        if hungry:
            self.maxSpeed = Predator.maxHungrySpeed
            # Still eating (immobile)
            if self.eating is not None:
                if self.eatCounter < Predator.eatDuration:
                    self.eatCounter += 1
                    if self.eatCounter % 10 == 0: # Blinking
                        if (self.eatCounter//10) % 2 == 0:
                            self.canvas.itemconfig(self.eating.id, state='normal')
                        else:
                            self.canvas.itemconfig(self.eating.id, state='hidden')
                else:
                    self.hunger -= Predator.nrgPerBoid
                    if DEBUG_LOG: print('Eaten boid:', self.id)
                    self.eating.killed()
                    self.eating = None
                    self.eatCounter = 0
                self.acc *= 0.
                self.vxt *= 0.
            # Look for boid
            else:
                closestBoid = self.getClosestBoid()
                if closestBoid is None: # Keep looking
                    self.acc += self.roam()
                else:
                    self.maxSpeed = Predator.maxHuntSpeed
                    sqrDist = closestBoid.distanceSqr(self)
                    # Close enough to eat
                    if sqrDist <= PRED_HH**2:
                        self.eating = closestBoid
                        self.eatCounter = 1
                        closestBoid.caught = True
                        print('Caught pred:', self.id)
                        self.acc *= 0.
                        self.vxt *= 0.
                    # Go toward boid
                    else:
                        self.hunger += Predator.hungerRate
                        
                        steer = vu.wrapRelativePos(self.pos, closestBoid.pos) - self.pos
                        steer = vu.setMag(steer, Predator.maxHuntSpeed)
                        steer -= self.vel
                        steer = vu.capMag(steer, Predator.maxForce*4.)
                        self.acc = steer
        
        return hungry
    
    
    #    
    def updatePos(self):
        # Compute forces
        self.acc *= self.inertiaRatio
        
        # Reproduction
        self.manageReproduction()
        
        # Starve
        if self.starved():
            return
        
        # Hungry
        hungry = self.manageHunger()
        
        # Roam free
        if not hungry:
            self.eating = None
            self.mating()
            self.acc += self.roam()
        
        # Special case: immobile -> random push
        if self.eating is None and vu.norm(self.acc) < EPSILON and vu.norm(self.vxt) < EPSILON:
            self.acc = vu.randomUnitVector() * Predator.maxForce
            # if DEBUG_LOG: print('Random push pred:', self.id)
        # No deceleration if not at full speed
        if vu.norm(self.vxt) < self.maxSpeed:
            self.inertiaRatio = 1.
        else:
            self.inertiaRatio = Predator.inertiaRatio
        
        # Apply acceleration
        self.acc = vu.capMag(self.acc, Predator.maxForce*4.) # Saturate acc
        self.vxt += self.acc
        self.vxt = vu.capMag(self.vxt, self.maxSpeed)  # Saturate vel
        self.nxt = np.add(self.nxt, self.vxt)
        
        # Update position + rotation
        if ((self.acc[0] != 0. or self.acc[1] != 0.)
            and (self.vxt[0] != 0. or self.vxt[1] != 0)):
            # Warp around
            vu.wrapEdges(self)
        
            self.points = vu.updateTriPoints(self.nxt, self.vel, PRED_HH, PRED_HW)
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

