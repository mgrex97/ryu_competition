#!/usr/bin/python3

import sys
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch

DEFAULT_SWITCH_SIZE = 42
MESH_SIZE = 30

class MinimalTopo( Topo ):
    "Minimal topology with a single switch and two hosts"
    def build( self ):
        self.addHost( 'h1' )
        self.addHost( 'h2' )

        for switch_index in range(DEFAULT_SWITCH_SIZE):
            self.addSwitch( 's' + str(switch_index + 1) , protocols='OpenFlow13' )

        for switch_index in range(MESH_SIZE):
            for siblings_switch_index in range(MESH_SIZE):
                if switch_index < siblings_switch_index:
                    self.addLink( 's' + str(switch_index + 13), 's' + str(siblings_switch_index + 13) )
            
        links = [
            (1,2),
            (1,5),
            (1,9),
            (2,3),
            (2,9),
            (2,13),
            (3,4),
            (3,5),
            (4,13),
            (5,6),
            (5,9),
            (5,12),
            (6,7),
            (7,13),
            (8,9),
            (9,10),
            (10,11),
            (10,12),
            (11,12),
            (12,13)
        ]
        

        for link in links:
            self.addLink( 's' + str(link[0]), 's' + str(link[1]) )

        self.addLink( 'h1', 's8' )
        self.addLink( 'h2', 's40' )


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
