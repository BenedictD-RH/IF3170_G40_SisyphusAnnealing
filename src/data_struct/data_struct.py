import json

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

    def getValuePerUnit(self) :
        return float(self.package.value)/self.package.getVolume()

    
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


class TruckState:
    def __init__(self, 
                 truck : Truck, 
                 packages : list[PackageState]) :
        self.truck = Truck(**truck) if isinstance(truck, dict) else truck
        self.packages = [(PackageState(**package) if isinstance(package, dict) else package) for package in packages]

    def to_json(self) :
        return json.dumps(to_dict(self), indent=4)

    def to_dict(self) :
        return to_dict(self)

    @classmethod
    def from_json(cls, jsonPath):
        with open(jsonPath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return cls(**data)

def getTotalValue(state : TruckState) :
    package_validity = [x.isFullyInTruck(state.truck.dimensions) for x in state.packages]

    # Cek buat intersection/overlap
    for i in range(len(state.packages)) :
        for j in range(i + 1, len(state.packages)) :
            if isIntersecting(state.packages[i], state.packages[j]) :
                package_validity[i] = False
                package_validity[j] = False
                break

    # Cek buat floating
    for i in range(len(state.packages)) :
        if package_validity[i] :
            is_supported = state.packages[i].coordinates["z"] == 0
            for j in range(len(state.packages)) : 
                if package_validity[j] and not is_supported and isStackedOn(state.packages[i], state.packages[j]):
                    is_supported = True
                    break
            if not is_supported :
                package_validity[i] = False

    # Cek buat fragility
    for i in range(len(state.packages)) :
        if package_validity[i] and state.packages[i].isFragile :
            for j in range(len(state.packages)) : 
                if isStackedOn(state.packages[j], state.packages[i]):
                    package_validity[i] = False
                    break

    total_value = 0
    for i in range(len(state.packages)) :
        if package_validity[i] :
            total_value += state.packages[i].package.value

    return total_value



def objectiveFunction(state : TruckState) :
    value = 0.0
    weight = 0
    maxValPerUnit = 0
    for p in state.packages :
        if p.isInTruck(state.truck.dimensions) :
            weight += p.getWeight()
            maxValPerUnit = max(maxValPerUnit, p.getValuePerUnit())
            for q in state.packages :
                if p.getID() != q.getID() and q.isInTruck(state.truck.dimensions) :
                    value -= 2*p.getValuePerUnit()*intersectingArea(p, q)
                #yg blm : floating, fragile, eta
            value += p.getValue() - 2*p.overflowVolume(state.truck.dimensions)*p.getValuePerUnit()


    return value - max(0, (weight - state.truck.maxCapacity)*maxValPerUnit)