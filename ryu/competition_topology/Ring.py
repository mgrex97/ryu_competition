#!/usr/bin/python3

import sys
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch

DEFAULT_SWITCH_SIZE = 48

class MinimalTopo( Topo ):
    "Minimal topology with a single switch and two hosts"
    def build( self ):

        pre_switch = None
        first_switch = None 
        for switch_index in range(DEFAULT_SWITCH_SIZE):
            # Create a switch
            switch = self.addSwitch( 's' + str(switch_index + 1) , protocols='OpenFlow13')

            # Get first switch
            if first_switch == None:
                first_switch = switch

            # Create a link connect to pre siwtch
            if pre_switch != None and switch_index != 0:
                self.addLink( pre_switch, switch )

            # Create a link for ring topology
            if switch_index == DEFAULT_SWITCH_SIZE - 1:
                self.addLink( first_switch, switch)

            # Get pre switch
            pre_switch = switch

        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
	self.addLink( 'h1', 's1' )
	self.addLink( 'h2', 's' + str(int(DEFAULT_SWITCH_SIZE / 2) + 1) )


def runMinimalTopo():
    "Bootstrap a Mininet network using the Minimal Topology"

    # Create an instance of our topology
    topo = MinimalTopo()

    # Create a network based on the topology using OVS and controlled by
    # a remote controller.
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController( name, ip='127.0.0.1' ),
        switch=OVSSwitch,
        autoSetMacs=True )

    # Actually start the network
    net.start()

    # Drop the user in to a CLI so user can run commands.
    CLI( net )

    # After the user exits the CLI, shutdown the network.
    net.stop()

if __name__ == '__main__':
    # This runs if this file is executed directly
    setLogLevel( 'info' )
    runMinimalTopo()

# Allows the file to be imported using `mn --custom <filename> --topo minimal`
topos = {
    'minimal': MinimalTopo
}
