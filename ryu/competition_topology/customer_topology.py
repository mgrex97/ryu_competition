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

class Tree( Topo ):
    def __init__(self, *args, **kwargs):
        self.level = kwargs.pop('level')
        self.link_size = 2 ** (self.level + 1) - 4
        super(Tree, self).__init__(*args, **kwargs)

    def build( self ):
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )

        for switch_index in range(1, 2 ** self.level):
            switch = self.addSwitch( 's' + str(switch_index) , protocols='OpenFlow13')

        parent_list = [1]
        for index in range(1, self.level):
            child_list = []
            while len(parent_list) != 0:
                parent = parent_list.pop()
                self.addLink('s' + str(parent), 's' + str(parent * 2))
                self.addLink('s' + str(parent), 's' + str(parent * 2 + 1))
                child_list.append(parent * 2 + 1)
                child_list.append(parent * 2)
            parent_list = child_list[::]

        self.addLink( 'h1', 's1')
        self.addLink( 'h2', 's' + str(2 ** self.level - 1))

class Competion_3_1( Topo ):
    def __init__(self, *args, **kwargs):
        self.level = 7
        self.link_size = 2 ** (self.level + 1) - 32
        super(Competion_3_1, self).__init__(*args, **kwargs)

    def build( self ):
        for switch_index in range(1, 2 ** self.level):
            switch = self.addSwitch( 's' + str(switch_index) , protocols='OpenFlow13')

        parent_list = [1]
        for index in range(1, self.level):
            child_list = []
            while len(parent_list) != 0:
                parent = parent_list.pop()
                if parent != 15:
                    self.addLink('s' + str(parent), 's' + str(parent * 2))
                    self.addLink('s' + str(parent), 's' + str(parent * 2 + 1))
                    child_list.append(parent * 2)
                    child_list.append(parent * 2 + 1)
            parent_list = child_list[::]

class Competion_4_2( Topo ):
    def __init__(self, *args, **kwargs):
        self.level = 6
        self.link_size = 98
        super(Competion_4_2, self).__init__(*args, **kwargs)

    def build( self ):
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )

        for switch_index in range(1, 2 ** self.level):
            switch = self.addSwitch( 's' + str(switch_index) , protocols='OpenFlow13')

        parent_list = [1]
        for index in range(1, self.level):
            child_list = []
            while len(parent_list) != 0:
                parent = parent_list.pop()
                if parent != 15 and parent != 12 and 29:
                    if parent != 14 and parent != 27:
                        self.addLink('s' + str(parent), 's' + str(parent * 2))
                        child_list.append(parent * 2)

                    self.addLink('s' + str(parent), 's' + str(parent * 2 + 1))
                    child_list.append(parent * 2 + 1)
            parent_list = child_list[::]

        switch = self.addSwitch( 's104', protocols='OpenFlow13')
        switch = self.addSwitch( 's105', protocols='OpenFlow13')
        switch = self.addSwitch( 's107', protocols='OpenFlow13')
        self.addLink( 's52', 's104')
        self.addLink( 's52', 's105')
        self.addLink( 's53', 's107')

        self.addLink( 'h1', 's33')
        self.addLink( 'h2', 's55')

class Competion_5_2( Topo ):
    def __init__(self, *args, **kwargs):
        self.link_size = 28
        super(Competion_5_2, self).__init__(*args, **kwargs)

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

