from aux.format import print_label
from aux.format import standard,line

def show_symmetry(symmetry):
    for i in range(symmetry['rotations'].shape[0]):
        print("  --------------- %4d ---------------" % (i + 1))
        rot = symmetry['rotations'][i]
        trans = symmetry['translations'][i]
        print("  rotation:")
        for x in rot:
            print("     [%2d %2d %2d]" % (x[0], x[1], x[2]))
        print("  translation:")
        print("     (%8.5f %8.5f %8.5f)" % (trans[0], trans[1], trans[2]))

def show_lattice(lattice):
    print("Basis vectors:")
    for vec, axis in zip(lattice, ("a", "b", "c")):
        print("%s %10.5f %10.5f %10.5f" % (tuple(axis,) + tuple(vec)))

def show_cell(lattice, positions, numbers):
    show_lattice(lattice)
    print("Atomic points:")
    for p, s in zip(positions, numbers):
        print("%2d %10.5f %10.5f %10.5f" % ((s,) + tuple(p)))

from aux.PeriodicTable import periodicTableElement
def print_line(line,**kwargs):
    kwargs = standard.fix(**kwargs)
    kwargs['stream'].write("|"+(line).center(kwargs['linewidth'])+"|"+"\n")

def get_equivalent_line(i,j,atom,wyck):
    output = "%s: "%(atom)
    output += " %d "%(i+1)+" -> "
    output += " %d "%(j+1)+" W: "
    output += "%s"%(wyck)
    return output

class WriteReport:
    def __init__(self, data,
                **kwargs):
        if 'comments' in kwargs:
            self.comments = kwargs['comments']
        else:
            self.comments=["" for record in data]
        self.kwargs = standard.fix(**kwargs)
        self.data   = data
        self.write()

    def write(self):
        line(**self.kwargs)
        print_label("Symmetry analysis",**self.kwargs)
        line(**self.kwargs)
        for i,record in enumerate(self.data):
            self.write_single(i,crystal=
                      [periodicTableElement[
                          record['std_types'][
                              mapping]-1]
                          for mapping in record['mapping_to_primitive']])
    def write_single(self,index,**kwargs):
        wyckoffCount   = dict.fromkeys(set(self.data[index]['wyckoffs']),0)
        print_line(self.comments[index],**self.kwargs)
        line(**self.kwargs)
        print_line("Spacegroup: %s (%d) "%(self.data[index]['international'],self.data[index]['number']),**self.kwargs)
        print_line("Mapping to equivalent atoms with the Wyckoff positions:",**self.kwargs)

        for i,(j,atom,wyck) in enumerate(zip(self.data[index]['equivalent_atoms'],
                                             kwargs['crystal'],
                                             self.data[index]['wyckoffs'])):
            output = get_equivalent_line(i,j,atom,wyck)
            print_line(output,**self.kwargs)
            wyckoffCount[wyck] += 1
        line(**self.kwargs)
        output = ""
        for wyck in wyckoffCount:
            output += " #%s  =  %d "%(wyck,wyckoffCount[wyck])
        print_line(output,**self.kwargs)
        line(**self.kwargs)
