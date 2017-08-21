#!/usr/bin/python3

from mininet.topo import Topo
base_switch_dpid = 4097


class Ring( Topo ):
    def __init__(self, *args, **kwargs):
        self.switch_size = kwargs.pop('switch_size')
        self.link_size = self.switch_size * 2
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
        self.link_size = self.switch_size * (self_size - 1) / 2
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
 


class Linear( Topo ):
    def __init__(self, *args, **kwargs):
        self.switch_size = kwargs.pop('switch_size')
        self.link_size = (self.switch_size - 1) * 2
        super(Linear, self).__init__(*args, **kwargs)

    def build( self ):
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )

        for switch_index in range(base_switch_dpid, base_switch_dpid + self.switch_size):
            switch = self.addSwitch( 's' + str(switch_index) , protocols='OpenFlow13')

        for switch_index in range(base_switch_dpid, base_switch_dpid + self.switch_size - 1):
            self.addLink( 's' + str(switch_index), 's' + str(switch_index + 1) )

        self.addLink( 'h1', 's4097' )
        self.addLink( 'h2', 's' + str(base_switch_dpid + self.switch_size - 1) )

class Competion_5_1( Topo ):
    def __init__(self, *args, **kwargs):
        self.link_size = 28
        super(Competion_5_1, self).__init__(*args, **kwargs)

    def build( self ):
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )

        for switch_index in range(11):
            switch = self.addSwitch( 's' + str(switch_index + 1) , protocols='OpenFlow13')

        links = [
            (1,2),
            (1,4),
            (2,3),
            (2,6),
            (3,8),
            (4,5),
            (4,9),
            (5,6),
            (6,7),
            (6,9),
            (7,8),
            (8,11),
            (9,10),
            (10,11)
        ]

        for link in links:
            self.addLink( 's' + str(link[0]), 's' + str(link[1]) )

        self.addLink( 'h1', 's4')
        self.addLink( 'h2', 's11')

class Competion_6_2( Topo ):
    def __init__(self, *args, **kwargs):
        self.link_size = 16
        super(Competion_6_2, self).__init__(*args, **kwargs)

    def build( self ):
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )

        for switch_index in range(base_switch_dpid, base_switch_dpid + 9):
            switch = self.addSwitch( 's' + str(switch_index) , protocols='OpenFlow13')

        links = [
            (0,1),
            (0,4),
            (1,2),
            (1,5),
            (5,6),
            (5,7),
            (7,8),
            (8,3)
        ]

        for link in links:
            self.addLink( 's' + str(base_switch_dpid + link[0]), 's' + str(base_switch_dpid + link[1]) )

        self.addLink( 'h1', 's' + str(base_switch_dpid) )
        self.addLink( 'h2', 's' + str(base_switch_dpid + 3) )

