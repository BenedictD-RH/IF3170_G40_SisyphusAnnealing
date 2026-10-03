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


class PackageState:
    def __init__(self, 
                 package : Package, 
                 coordinates : dict[str, int], 
                 orientation : dict[str, int]) :
        self.package = Package(**package) if isinstance(package, dict) else package
        self.coordinates = coordinates
        self.orientation = orientation

    def isIntersecting(self, other) :
        
        return True


class TruckState:
    def __init__(self, 
                 truck : Truck, 
                 packages : list[PackageState]) :
        self.truck = Truck(**truck) if isinstance(truck, dict) else Truck
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

def objectiveFunction(self) :

    return 0