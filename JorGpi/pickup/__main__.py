#!/usr/bin/python3
# -*- coding: utf-8 -*-

from sys import argv
import time

from JorGpi.pickup.pickup import SmartPickUp,Reference,CommandLineOptions

if __name__ == '__main__':
    tracker  = -(time.time())
    options = CommandLineOptions(*argv)

    elements = ''.join(options('elements'))
    ref = Reference(options('reference')+"/POSCAR")

    print("Running for NN=%d, \'%s\' from atom No %d:"%(options('number_of_interactions'),
                                                        elements,ref()))
    pickerUpper = SmartPickUp(options('number_of_interactions'),elements)
    pickerUpper.read(options('reference'),*options('directories'),reference=ref())

    print("Exchange interaction magnitude(s) in %s:"%options('units'))
    pickerUpper.solve(units=options('units'))
    print(pickerUpper)

    tracker += time.time()
    hours    = int(tracker/3600)
    minutes  = int(tracker/60) - hours*60
    seconds  = int(tracker) - (minutes + hours*60)*60,
    nanosec  = int(1e9*(tracker-int(tracker)))
    print("Runntime of %02d:%02d:%02d.%09d"%(  hours, minutes,
                                             seconds, nanosec))