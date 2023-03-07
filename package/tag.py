from itemset import ItemsetFlyweight
import logging

class Tagger:

    _next = None
    name = ""
    _params = dict()
    _map = dict()

    def setNext(self, tag):
        
        lastObj = self
        while lastObj._next is not None:
            lastObj = lastObj._next
        
        lastObj._next = tag
        self._map[type(tag).__name__] = tag

    def getNext(self):
        return self._next
    
    def setParams(self, param=dict(), **kwargs):
        for k, v in param.items():
            self._params[k] = v

        for k, v in kwargs.items():
            self._params[k] = v
        
    def tag(self, param, **kwargs):
        ''' implement in child class'''
        if self._next:
            self._next.tag(param, **kwargs)

class TagMainItemset(Tagger):
    def __init__(self):
        self.table = dict()
        self.name = "mainItemset"

    def __getitem__(self, group):
        return self.table[group]

    def tag(self, params=dict(), **kwargs):
        for k, v in kwargs.items():
            params[k] = v

        itemset = params["mainItemset"]
        node_id = params["node_id"]
        seed = self._params["belonging"][node_id]
        expectedProbability = self._params["expectedProbability"][seed][node_id]
        ids = str(itemset)

        if seed not in self.table:
            self.table[seed] = dict()
        
        if ids not in self.table[seed]:
            self.table[seed][ids] = expectedProbability
        else:
            self.table[seed][ids] += expectedProbability

        
        # Temporarily delete the key which is None
        for group in self.table.keys():
            if "None" in self.table[group]:
                del self.table[group]["None"]

        super().tag(params)

    def maxExcepted(self, group):
        if len(self.table[group]) == 0:
            return None
        return max(self.table[group], key=self.table[group].get)
    
class TagAppending(Tagger):
    '''
        Appending 與 Addtional 不同, Appeding是沒有優惠方案下與主商品搭配時, 效益最高的附加品。
    '''
    def __init__(self, itemset:ItemsetFlyweight):
        self.table = dict()
        self._itemset = itemset
        self.name = "appending"

    def __iter__(self):
        for seed, exceptedAppending in self.table.items():
            yield seed, exceptedAppending
    
    def __getitem__(self, group):
        return self.table[group]
    
    def tag(self, params=dict(), **kwargs):
        for k, v in kwargs.items():
            params[k] = v
            
        node_id = params["node_id"]
        mainItemset = params["mainItemset"]
        seed = self._params["belonging"][node_id]
        expectedProbability = self._params["expectedProbability"][seed][node_id]

        if seed not in self.table:
            self.table[seed] = dict()
        
        obj = self._itemset.maxSupersetValue(params["node"]["topic"], mainItemset)
        logging.debug("Node: {0}, Maxum benfit itemset: {1}, Probability {2}".format(node_id, str(obj), expectedProbability))

        addItemset = self._itemset.difference(obj, mainItemset)
        ids = str(addItemset)

        if ids not in self.table[seed]:
            self.table[seed][ids] = expectedProbability
        else:
            self.table[seed][ids] += expectedProbability

        # Temporarily delete the key which is None
        for group in self.table.keys():
            if "None" in self.table[group]:
                del self.table[group]["None"]
                
        super().tag(params)
    
    def maxExcepted(self, group):
        if len(self.table[group]) == 0:
            return None
        
        return max(self.table[group], key=self.table[group].get)

class TagRevenue(Tagger):
    def __init__(self):
        self._counting = 0
        
    def tag(self, params, **kwargs):
        for k, v in kwargs.items():
            params[k] = v

        self._counting += params["amount"]
        return super().tag(params, **kwargs)

    def amount(self):
        return self._counting