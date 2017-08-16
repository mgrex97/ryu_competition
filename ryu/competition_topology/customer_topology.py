#!/usr/bin/python3

from mininet.topo import Topo

class Ring( Topo ):
    def __init__(self, *args, **kwargs):
        self.switch_size = kwargs.pop('switch_size')
        super(Ring, self).__init__(*args, **kwargs)

    def build( self ):
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )

        pre_switch = None
        first_switch = None 
        for switch_index in range(self.switch_size):
            # Create a switch
            switch = self.addSwitch( 's' + str(switch_index + 1) , protocols='OpenFlow13')

            # Get first switch
            if first_switch == None:
                first_switch = switch

            # Create a link connect to pre siwtch
            if pre_switch != None and switch_index != 0:
                self.addLink( pre_switch, switch )

            # Create a link for ring topology
            if switch_index == self.switch_size - 1:
                self.addLink( first_switch, switch)

            # Get pre switch
            pre_switch = switch

        self.addLink( 'h1', 's1' )
        self.addLink( 'h2', 's' + str(int(self.switch_size / 2)) )

class Mesh( Topo ):
    def __init__(self, *args, **kwargs):
        self.switch_size = kwargs.pop('switch_size')
        super(Mesh, self).__init__(*args, **kwargs)

    def build( self ):
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )

        for switch_index in range(1, self.switch_size + 1):
            switch = self.addSwitch( 's' + str(switch_index) , protocols='OpenFlow13')

        for switch_index in range(1, self.switch_size + 1):
            for siblings_switch_index in range(1, self.switch_size + 1):
                if switch_index < siblings_switch_index:
                    self.addLink( 's' + str(switch_index), 's' + str(siblings_switch_index) )

	    self.addLink( 'h1', 's1' )
	    self.addLink( 'h2', 's' + str(int(self.switch_size / 2)) )
 
