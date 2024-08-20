import re

from enum import Enum
from tmnpy.dsl.element import Element

class TMNTSerializer(object):

    """
    The TMNTSerializer is a serializer that could take in a DSL object or a 
    list of objects and later convert it into a dictionary.

    Parameters
    ----------
    none    
    """

    def serialize(self, element, pos, result_dict):
        """
        This is a recursive function that serializes a single element. 

        Parameters
        ----------
        element: object
            Any DSL object
        pos: int
            Position of the recurive function in the element's dictionary form
        result_dict: dict
            New dictionary that stores contents of the elements
            
        Return
        ------
        A complete representation of the element as a dictionary (result_dict)
        """
        #add "type" key
        type_name = type(element).__name__
        if (
            (type_name == "Asset") or \
            (type_name == "Actor") or \
            (type_name == "Boundary") or \
            (type_name == "DataFlow") or \
            (type_name == "ExternalEntity") or \
            (type_name == "Process") or \
            (type_name == "WorkFlow")
        ):
            result_dict["type"] = type_name

        elem_dict = element.__dict__
        #base case: looked through all contents of element
        keys = list(elem_dict.keys())
        if pos >= len(keys) or pos < 0:
            return result_dict
        else:
            #removing unnecessary characters from key 
            if "__" in keys[pos]: 
                index = re.search("__", keys[pos]).end()
                key = keys[pos][index:]
            else:
                key = keys[pos]

            new_elem = elem_dict[keys[pos]]
            try:
                #check to see if value needs to be recursed
                new_elem.__dict__
                if isinstance(new_elem, Enum):
                    raise AttributeError
            except AttributeError:
                #if value is an instance of a list (e.g. Data)
                if (isinstance(new_elem, list)) and (len(new_elem) > 0):
                    if isinstance(new_elem[0], Element):
                        obj_lst = []
                        for obj in new_elem:
                            obj_lst.append(self.serialize(obj, 0, {}))
                        result_dict[key] = obj_lst
                    else:
                        result_dict[key] = new_elem
                #clean out empty values
                elif (
                    (new_elem != None) and \
                    (new_elem != "N/A") and \
                    (new_elem != []) and \
                    (new_elem != set())
                ):
                    result_dict[key] = new_elem
            else:
                result_dict[key] = self.serialize(new_elem, 0, {})
                
            return self.serialize(element, pos+1, result_dict)


    def serialize_list(self, lst, result_dict):
        """
        This is a recursive function that serializes a list of elements. 

        Parameters
        ----------
        lst: list
            List of DSL object
        result_dict: dict
            New dictionary with a list of serialized DSL objects as its value
            
        Return
        ------
        A complete representation of the list of elements as a dictionary 
        (result_dict)
        """
        #iterate through list & recurse each element
        elem_lst = []
        for elem in lst:
            elem_lst.append(self.serialize(elem, 0, {}))
        
        #add "type" key
        type_name = type(lst[0]).__name__
        if ((type_name == "DataFlow") or (type_name == "WorkFlow")):
            result_dict["flows"] = elem_lst
        elif (type_name[-1] == "y"):
            name = type_name[:-1].lower() + "ies"
            result_dict[name] = elem_lst
        else:
            name = type_name.lower() + "s"
            result_dict[name] = elem_lst
            
        return result_dict
    