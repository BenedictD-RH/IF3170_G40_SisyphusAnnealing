import json
import math
import copy
import random
import numpy as np

def to_dict(obj):
    if isinstance(obj, (list, tuple)):
        return [to_dict(item) for item in obj]
    
    elif hasattr(obj, "__dict__"):
        return {key: to_dict(value) for key, value in obj.__dict__.items()}
    
    elif isinstance(obj, dict):
        return {key: to_dict(value) for key, value in obj.items()}
    
    return obj

class Truck:
    def __init__(self, 
                 dimensions : dict[str, int], 
                 maxCapacity : int) :
        self.dimensions = dimensions
        self.maxCapacity = maxCapacity

    def getSurfaceArea(self) :
        w = self.dimensions['w']
        l = self.dimensions['l'] 
        h = self.dimensions['h']

        return 2 * w * l + 2 * w * h + 2 * l * h

class Package:
    def __init__(self, 
                 id : str, 
                 dimensions : dict[str, int], 
                 value : int, 
                 weight : int, 
                 isFragile : bool, 
                 eta : int) :
        self.id = id
        self.dimensions = dimensions
        self.value = value
        self.weight = weight
        self.isFragile = isFragile
        self.eta = eta

    def getVolume(self) :
        return self.dimensions['w'] * self.dimensions['l'] * self.dimensions['h']
        

    def getValuePerUnit(self) :
        vol = self.getVolume()
        return float(self.value) / vol if vol > 0 else 0.0

    def getSurfaceArea(self) :
        w = self.dimensions['w']
        l = self.dimensions['l'] 
        h = self.dimensions['h']

        return 2 * w * l + 2 * w * h + 2 * l * h

class PackageState:
    def __init__(self, 
                 package : Package, 
                 coordinates : dict[str, int], 
                 orientation : dict[str, int]) :
        self.package = Package(**package) if isinstance(package, dict) else package
        self.coordinates = coordinates
        self.orientation = orientation

    def getAbsoluteBB(self) :
        x = self.coordinates["x"]
        y = self.coordinates["y"]
        z = self.coordinates["z"]
        x2 = x + self.package.dimensions[self.orientation["x"]]
        y2 = y + self.package.dimensions[self.orientation["y"]]
        z2 = z + self.package.dimensions[self.orientation["z"]]

        return (x, y, z, x2, y2, z2)

    def isInTruck(self, truckdim) :
        return (self.coordinates['x'] >= 0 and truckdim['w'] > self.coordinates['x'] and
                self.coordinates['y'] >= 0 and truckdim['l'] > self.coordinates['y'] and
                self.coordinates['z'] >= 0 and truckdim['h'] > self.coordinates['z'])

    def overflowVolume(self, truckdim) :
        bb = self.getAbsoluteBB()
        w = max(0, min(truckdim["w"] - bb[0], bb[3], bb[3] - bb[0], truckdim["w"]))
        l = max(0, min(truckdim["l"] - bb[1], bb[4], bb[4] - bb[1], truckdim["l"]))
        h = max(0, min(truckdim["h"] - bb[2], bb[5], bb[5] - bb[2], truckdim["h"]))
    
        return self.package.getVolume() - w*l*h

    def isFullyInTruck(self, truckdim) :
        return self.overflowVolume(truckdim) == 0 and self.isInTruck(truckdim)
        

    def getID(self) :
        return self.package.id

    def isFragile(self) :
        return self.package.isFragile

    def getValue(self) :
        return self.package.value

    def getWeight(self) :
        return self.package.weight

    def getETA(self) :
        return self.package.eta

    def getValuePerUnit(self) :
        return float(self.package.value)/self.package.getVolume()

    def getSurfaceArea(self) :
        return self.package.getSurfaceArea()

    def getStateString(self) :
        x = self.coordinates["x"]
        y = self.coordinates["y"]
        z = self.coordinates["z"]
        w = self.package.dimensions[self.orientation["x"]]
        l = self.package.dimensions[self.orientation["y"]]
        h = self.package.dimensions[self.orientation["z"]]
        return f"""ID = {self.getID()}
        Coordinates = (x: {x}, y: {y}, z: {z})
        Orientation = (x: {self.orientation["x"]}, y: {self.orientation["y"]}, z: {self.orientation["z"]})
        Dimensions = (w: {w}, l: {l}, h: {h})
        Value = {self.getValue()}
        Weight = {self.getWeight()}
        Fragile = {self.isFragile()}
        ETA = {self.getETA()}"""

    
def intersectingArea(p1 : PackageState, p2 : PackageState) :
    bb1 = p1.getAbsoluteBB()
    bb2 = p2.getAbsoluteBB()
    w = max(0, min(bb2[3] - bb1[0], bb1[3] - bb2[0], bb1[3] - bb1[0], bb2[3] - bb2[0]))
    l = max(0, min(bb2[4] - bb1[1], bb1[4] - bb2[1], bb1[4] - bb1[1], bb2[4] - bb2[1]))
    h = max(0, min(bb2[5] - bb1[2], bb1[5] - bb2[2], bb1[5] - bb1[2], bb2[5] - bb2[2]))

    return w * l * h

def isIntersecting(p1 : PackageState, p2 : PackageState) :
    return intersectingArea(p1, p2) > 0

def isStackedOn(top : PackageState, bottom : PackageState) :
    top_bb = top.getAbsoluteBB()
    bottom_bb = bottom.getAbsoluteBB()

    if (top_bb[0] >= bottom_bb[3] or bottom_bb[0] >= top_bb[3] or
        top_bb[1] >= bottom_bb[4] or bottom_bb[1] >= top_bb[4]) :
        return False

    return top_bb[2] == bottom_bb[5]

def nearestSupportDistance(top : PackageState, support : PackageState) :
    top_bb = top.getAbsoluteBB()
    sprt_bb = support.getAbsoluteBB()

    w = max(0, -min(sprt_bb[3] - 1 - top_bb[0], top_bb[3] - sprt_bb[0] - 1, top_bb[3] - top_bb[0], sprt_bb[3] - sprt_bb[0]))
    l = max(0, -min(sprt_bb[4] - 1 - top_bb[1], top_bb[4] - sprt_bb[1] - 1, top_bb[4] - top_bb[1], sprt_bb[4] - sprt_bb[1]))
    h = sprt_bb[5] - top_bb[2]

    return math.sqrt(pow(w, 2) + pow(l, 2) + pow(h, 2))

def supportedArea(top : PackageState, support : PackageState) :
    top_bb = top.getAbsoluteBB()
    sprt_bb = support.getAbsoluteBB()
    w = max(0, min(sprt_bb[3] - top_bb[0], top_bb[3] - sprt_bb[0], top_bb[3] - top_bb[0], sprt_bb[3] - sprt_bb[0]))
    l = max(0, min(sprt_bb[4] - top_bb[1], top_bb[4] - sprt_bb[1], top_bb[4] - top_bb[1], sprt_bb[4] - sprt_bb[1]))
    h = sprt_bb[5] - sprt_bb[2] if top_bb[2] == sprt_bb[5] else 0 

    return w * l * h

def canBeSupport(top: PackageState, support : PackageState, truckdim) :
    total_height = support.coordinates['z'] + support.package.dimensions[support.orientation['z']] + top.package.dimensions[top.orientation['z']]
    return total_height <= truckdim['h'] and not(support.isFragile())

def contactArea(p1 : PackageState, p2 : PackageState) :
    bb1 = p1.getAbsoluteBB()
    bb2 = p2.getAbsoluteBB()

    total = 0
    if bb1[0] == bb2[3] or bb2[0] == bb1[3] :
        l = max(0, min(bb2[4] - bb1[1], bb1[4] - bb2[1], bb1[4] - bb1[1]))
        h = max(0, min(bb2[5] - bb1[2], bb1[5] - bb2[2], bb1[5] - bb1[2]))
        total += l * h
    if bb1[1] == bb2[4] or bb2[1] == bb1[4] :
        w = max(0, min(bb2[3] - bb1[0], bb1[3] - bb2[0], bb1[3] - bb1[0]))
        h = max(0, min(bb2[5] - bb1[2], bb1[5] - bb2[2], bb1[5] - bb1[2]))
        total += w * h
    if bb1[2] == bb2[5] :
        w = max(0, min(bb2[3] - bb1[0], bb1[3] - bb2[0], bb1[3] - bb1[0]))
        l = max(0, min(bb2[4] - bb1[1], bb1[4] - bb2[1], bb1[4] - bb1[1]))
        total += w * l * 2
    

    return total

def contactAreaTruck(p : PackageState, truckdim) :
    bb = p.getAbsoluteBB()
    w = bb[3] - bb[0]
    l = bb[4] - bb[1]
    h = bb[5] - bb[2]

    total = 0
    if bb[0] == 0 :
        total += l * h
    if bb[3] == truckdim['w'] :
        total += w * h
    if bb[1] == 0 :
        total += w * h
    if bb[4] == truckdim['l'] :
        total += w * h
    if bb[2] == 0 :
        if p.isFragile() :
            total += w * l
        else :
            total += w * l * 2

    return total

def isBehindOrBelow(p1 : PackageState, p2 : PackageState) :
    bb1 = p1.getAbsoluteBB()
    bb2 = p2.getAbsoluteBB()
    w = max(0, min(bb2[3] - bb1[0], bb1[3] - bb2[0], bb1[3] - bb1[0], bb2[3] - bb2[0]))
    l = max(0, min(bb2[4] - bb1[1], bb1[4] - bb2[1], bb1[4] - bb1[1], bb2[4] - bb2[1]))
    h = max(0, min(bb2[5] - bb1[2], bb1[5] - bb2[2], bb1[5] - bb1[2], bb2[5] - bb2[2]))

    if l * h and bb1[0] > bb2[0] :
        return True

    if w * l and bb1[2] < bb2[2] :
        return True

    return False

def getETAWeight(p : PackageState, truckdim, maxETA) :
    x = p.coordinates["x"]
    y = p.coordinates["y"]
    z = p.coordinates["z"]
    w = p.package.dimensions[p.orientation["x"]]
    l = p.package.dimensions[p.orientation["y"]]
    h = p.package.dimensions[p.orientation["z"]]        
    max_w = truckdim['w']
    max_l = truckdim['l']
    max_h = truckdim['h']

    return (1 - abs(float(x)/(max_w - w) - (float(p.getETA())/maxETA))) * (1 - abs((float(max_h - (z + h))/(max_h)) - (float(p.getETA())/maxETA)))

    

class TruckState:
    def __init__(self, 
                 truck : Truck, 
                 packages : list[PackageState]) :
        self.truck = Truck(**truck) if isinstance(truck, dict) else truck
        self.packages = [(PackageState(**package) if isinstance(package, dict) else package) for package in packages]

    def clone(self) -> "TruckState":
        pkgs = [PackageState(p.package, dict(p.coordinates), dict(p.orientation)) for p in self.packages]
        return TruckState(self.truck, pkgs)

    def __copy__(self):
        return self.clone()

    def to_json(self) :
        return json.dumps(to_dict(self), indent=4)

    def to_dict(self) :
        return to_dict(self)

    @classmethod
    def from_json(cls, jsonPath):
        with open(jsonPath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return cls(**data)

    def getSpaceMatrix(self) :
        space_matrix = np.zeros((self.truck.dimensions['w'], self.truck.dimensions['l'], self.truck.dimensions['h']))
        for pkg in self.packages :
            if pkg.isInTruck(self.truck.dimensions) :
                bb = pkg.getAbsoluteBB()
                for x in range(bb[0], min(bb[3], self.truck.dimensions['w'])) :
                    for y in range(bb[1], min(bb[4], self.truck.dimensions['l'])) :
                        for z in range(bb[2], min(bb[5], self.truck.dimensions['h'])) :
                            if pkg.isFragile() :
                                space_matrix[x][y][z] = -1
                            else :
                                space_matrix[x][y][z] = 1

        return space_matrix

    def generate_random_state(self, outside_prob: float = 0.2) -> "TruckState":
        import random
        rand_state = copy.deepcopy(self)
        truck_dims = rand_state.truck.dimensions
        axes_dims = ["w", "l", "h"]

        for pkg in rand_state.packages:
            # Acak orientasi dimensi
            d = axes_dims.copy()
            random.shuffle(d)
            pkg.orientation = {"x": d[0], "y": d[1], "z": d[2]}

            # Tentukan apakah berada di dalam atau di luar peti kemas
            if random.random() < outside_prob:
                pkg.coordinates = {"x": -1, "y": -1, "z": -1}
            else:
                pkg.coordinates = {
                    "x": random.randint(0, max(0, truck_dims.get("w", 10) - 1)),
                    "y": random.randint(0, max(0, truck_dims.get("l", 10) - 1)),
                    "z": random.randint(0, max(0, truck_dims.get("h", 10) - 1))
                }

        return rand_state

def getTotalValue(state : TruckState) :
    value = 0.0
    for p in state.packages :
        if p.isInTruck(state.truck.dimensions) :
            nearestSupport = p.coordinates['z']
            intersecting = 0
            overflow = p.overflowVolume(state.truck.dimensions)
            supportingArea = 0
            lateness = 0
            for q in state.packages :
                if p.getID() != q.getID() and q.isInTruck(state.truck.dimensions) :
                    intersecting += intersectingArea(p, q)*0.25
                    if canBeSupport(p, q, state.truck.dimensions) :
                        nearestSupport = min(nearestSupport, nearestSupportDistance(p, q))
                    if p.isFragile() :
                        supportingArea += supportedArea(q, p)
                    if isBehindOrBelow(p, q) and p.getETA() < q.getETA() :
                        lateness = max(lateness, q.getETA() - p.getETA())
                
            valid = 0 if nearestSupport or overflow or intersecting or supportingArea else 1
            # if not valid :
            #     print(p.getID())
            #     print("intersecting : " + str(intersecting))
            #     print("nearestSupport : " + str(nearestSupport))
            #     print("overflow : " + str(overflow))
            #     print("supportingArea : " + str(supportingArea))
            #     print("lateness : " + str(lateness))

            value += p.getValue()*valid
        # else :
            # print(p.getID())
            # print(p.coordinates)


    return value

def isValid(state : TruckState) :
    weight = 0
    for p in state.packages :
        if p.isInTruck(state.truck.dimensions) :
            weight += p.getWeight()
            nearestSupport = p.coordinates['z']
            intersecting = 0
            overflow = p.overflowVolume(state.truck.dimensions)
            supportingArea = 0
            lateness = 0
            for q in state.packages :
                if p.getID() != q.getID() and q.isInTruck(state.truck.dimensions) :
                    intersecting += intersectingArea(p, q)*0.25
                    if canBeSupport(p, q, state.truck.dimensions) :
                        nearestSupport = min(nearestSupport, nearestSupportDistance(p, q))
                    if p.isFragile() :
                        supportingArea += supportedArea(q, p)
                    if isBehindOrBelow(p, q) and p.getETA() < q.getETA() :
                        lateness = max(lateness, q.getETA() - p.getETA())
                
            valid = 0 if nearestSupport or overflow or intersecting or supportingArea else 1
            if not valid : 
                return False

    return weight < state.truck.maxCapacity

def getTotalWeight(state : TruckState) :
    weight = 0
    for p in state.packages :
        if p.isInTruck(state.truck.dimensions) :
            weight += p.getWeight()

    return weight

def objectiveFunction(state : TruckState) :
    value = 0.0
    weight = 0
    maxValPerUnit = 0
    truckTotalSurface = 0
    penalty = 0
    maxETA = 0
    for p in state.packages :
        maxETA = max(maxETA, p.getETA())

    for p in state.packages :
        if p.isInTruck(state.truck.dimensions) :
            weight += p.getWeight()
            maxValPerUnit = max(maxValPerUnit, p.getValuePerUnit())
            nearestSupport = p.coordinates['z']
            intersecting = 0
            overflow = p.overflowVolume(state.truck.dimensions)
            supportingArea = 0
            surfaceContact = contactAreaTruck(p, state.truck.dimensions)
            truckTotalSurface += contactAreaTruck(p, state.truck.dimensions)
            amount = 0
            late_amount = 0
            for q in state.packages :
                if p.getID() != q.getID() and q.isInTruck(state.truck.dimensions) :
                    intersecting += intersectingArea(p, q)*0.25
                    if canBeSupport(p, q, state.truck.dimensions) :
                        nearestSupport = min(nearestSupport, nearestSupportDistance(p, q))
                    if p.isFragile() :
                        supportingArea += supportedArea(q, p)
                    surfaceContact += contactArea(p, q)
                    if isBehindOrBelow(p, q) :
                        amount += 1
                        if p.getETA() < q.getETA() :
                            late_amount += 1
                        
            max_p_height = state.truck.dimensions['h'] - p.package.dimensions[p.orientation['z']]
            fragilePlacement = (max_p_height - p.coordinates['z'])/max_p_height if p.isFragile() else 0
            valid = 0 if nearestSupport or supportingArea else 1
            lateness = (1 - late_amount/amount) if amount > 0 else 1
            multiplier = (0.9 + 0.05*(surfaceContact)/p.getSurfaceArea() + 0.05*(1 - fragilePlacement))
            value += p.getValue()*valid*multiplier
            penalty += (overflow*2 + nearestSupport + intersecting + supportingArea)*p.getValuePerUnit()

    value *= (0.9975 + 0.0025*float(truckTotalSurface)/state.truck.getSurfaceArea())
    penalty += max(0, (weight - state.truck.maxCapacity)*maxValPerUnit*10)
    return value - penalty