import math
import random
import numpy as np
# Project
from constants import *

"""A set of useful vector util functions"""

#
def norm(vec):
    return math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])

#
def normalize(vec):
    vecLen = norm(vec)
    if vecLen > EPSILON:
        return vec / vecLen
    else:
        return vec

#
def setMag(vec, val):
    vec = normalize(vec)
    return vec * val

#
def capMag(vec, val):
    vecLen = norm(vec)
    if vecLen > val:
        return (vec / vecLen) * val
        
    return vec

#
def randomUnitVector():
    vec = np.array([ random.uniform(-1., 1.),
                     random.uniform(-1., 1.) ])
    return normalize(vec)

#
def distanceSqrWrapped(posA, posB):
    diff = posA - posB
    # Warp
    diff = np.absolute(diff)
    if diff[0] > CANVAS_W/2.: diff[0] = CANVAS_W - diff[0]
    if diff[1] > CANVAS_H/2.: diff[1] = CANVAS_H - diff[1]

    return diff[0]**2 + diff[1]**2
    
#
def wrapEdges(item, wrapPoints=False):
    if item.nxt[0] >= CANVAS_W:
        item.nxt[0] -= CANVAS_W
        if wrapPoints:
            item.points[0] -= CANVAS_W
            item.points[2] -= CANVAS_W
            item.points[4] -= CANVAS_W
    elif item.nxt[0] < 0:
        item.nxt[0] += CANVAS_W
        if wrapPoints:
            item.points[0] += CANVAS_W
            item.points[2] += CANVAS_W
            item.points[4] += CANVAS_W
        
    if item.nxt[1] >= CANVAS_H:
        item.nxt[1] -= CANVAS_H
        if wrapPoints:
            item.points[1] -= CANVAS_H
            item.points[3] -= CANVAS_H
            item.points[5] -= CANVAS_H
    elif item.nxt[1] < 0:
        item.nxt[1] += CANVAS_H
        if wrapPoints:
            item.points[1] += CANVAS_H
            item.points[3] += CANVAS_H
            item.points[5] += CANVAS_H

# 
def wrapRelativePos(refPos, otherPos):
    wrapPos = np.copy(otherPos)
    diff = refPos - otherPos
    # Warp
    diff = np.absolute(diff)
    if diff[0] > CANVAS_W/2.:
        if wrapPos[0] > CANVAS_W/2.:
            wrapPos[0] -= CANVAS_W
        else:
            wrapPos[0] += CANVAS_W
        
    if diff[1] > CANVAS_H/2.:
        if wrapPos[1] > CANVAS_H/2.:
            wrapPos[1] -= CANVAS_H
        else:
            wrapPos[1] += CANVAS_H
    
    return wrapPos

#
def getAdjacentPos(pos, minDist, maxDist=0, randChance=0):
    # Chance for random instead
    if randChance > 0:
        randPos = random.uniform(0., 1.) <= randChance
        if randPos:
            return np.array([ random.randint(0, CANVAS_W-1),
                              random.randint(0, CANVAS_H-1) ])
    # Adjacent
    vec = randomUnitVector()
    if maxDist > 0:
        vec *= random.uniform(minDist, maxDist)
    else:
        vec *= minDist
    vec += pos
    # Warp
    if vec[0] <  0.:       vec[0] += CANVAS_W
    if vec[0] >= CANVAS_W: vec[0] -= CANVAS_W
    if vec[1] <  0.:       vec[1] += CANVAS_H
    if vec[1] >= CANVAS_H: vec[1] -= CANVAS_H
    
    return vec
    
#
def getNearCellsFromPos(pos, radius, maxX, maxY):
    # Center
    gridX1, gridY1 = int(pos[0] // radius), int(pos[1] // radius)
    
    # Warp
    gridX0 = gridX1 - 1
    if gridX0 < 0: gridX0 = maxX
    gridX2 = gridX1 + 1
    if gridX2 > maxX: gridX2 = 0
    
    gridY0 = gridY1 - 1
    if gridY0 < 0: gridY0 = maxY
    gridY2 = gridY1 + 1
    if gridY2 > maxY: gridY2 = 0
    
    res = [ [gridX0, gridY0], [gridX0, gridY1], [gridX0, gridY2],
            [gridX1, gridY0], [gridX1, gridY1], [gridX1, gridY2],
            [gridX2, gridY0], [gridX2, gridY1], [gridX2, gridY2] ]
    
    return res

#
def updateTriPoints(pos, vel, halfHeight, halfWidth):
    # Compute new triangle points from 'pos' and 'vel' direction
    nVel = normalize(vel)
    nVelOrtho = np.array([-nVel[1], nVel[0]])
    
    head = pos + nVel*halfHeight
    base = pos - nVel*halfHeight
    first  = base + nVelOrtho*halfWidth
    second = base - nVelOrtho*halfWidth
    
    # Set
    return [ first[0],  first[1],
             head[0],   head[1],
             second[0], second[1] ]

