#!/usr/bin/python3

import sys
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch

DEFAULT_SWITCH_SIZE = 20

class MinimalTopo( Topo ):
    "Minimal topology with a single switch and two hosts"
    def build( self ):
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        
        for switch_index in range(11):
            switch = self.addSwitch( 's' + str(switch_index + 1) , protocols='OpenFlow13')
       
        links = [
            (1,2),
            (2,3),
            (4,5),
            (5,6),
            (6,7),
            (7,8),
            (9,10),
            (10,11),
            (3,8),
            (2,6),
            (1,4),
            (4,9),
            (6,9),
            (8,11),
        ]

        for link in links:
            self.addLink( 's' + str(link[0]), 's' + str(link[1]) )

        self.addLink( 'h1', 's4')
        self.addLink( 'h2', 's11')

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
