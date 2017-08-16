#!/usr/bin/python3

import sys
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch
from mininet.clean import Cleanup


from time import sleep
import json
import requests

class MinimalTopo( Topo ):
    "Minimal topology with a single switch and two hosts"
    def build( self ):
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        
        for switch_index in range(1, 12):
            switch = self.addSwitch( 's' + str(switch_index) , protocols='OpenFlow13')
       
        links = [
            (10,11),
            (11,8),
            (7,8),
            (3,8),
            (2,3),
            (6,7),
            (9,10),
            (6,9),
            (5,6),
            (1,2),
            (1,4),
            (4,5),
            (4,9),
        ]

        for link in links:
            self.addLink( 's' + str(link[0]), 's' + str(link[1]) )

        self.addLink( 'h1', 's4')
        self.addLink( 'h2', 's11')

def _curl_links(controller_ip='127.0.0.1'):
    try:
        r = requests.get('http://' + controller_ip + ':9191/topology')
        d = json.loads(r.content.decode('utf-8'))
        return d['links']
    except requests.ConnectionError:
        print("can't connect")
        exit()
    except UnboundLocalError:
        print("requests error")  
        exit()
        


def runMinimalTopo():
    "Bootstrap a Mininet network using the Minimal Topology"

    Cleanup.cleanup()

    # Create an instance of our topology
    topo = MinimalTopo()

    # Create a network based on the topology using OVS and controlled by
    # a remote controller.
    controller_ip = '127.0.0.1'
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController( name, ip=controller_ip ),
        switch=OVSSwitch,
        autoSetMacs=True )

    # Actually start the network
    net.start()

    Links_Count = len(_curl_links(controller_ip))
    while Links_Count != 26:
        sleep(2)
        Links_Count = len(_curl_links(controller_ip))
    print("Link Count : ", Links_Count)

    # Drop the user in to a CLI so user can run commands.
    h1, h2 = net.get( 'h1', 'h2' )
    h2.cmd('nohup ~/ryu/ryu/competition_topology/server.sh > ~/temp.log &')
    h1.cmd('nohup ~/ryu/ryu/competition_topology/send.sh 10.0.0.2 40 > /dev/null 2>&1 &')
    sleep(5)
    net.configLinkStatus('s4','s9','down')
    print('s4 - s9 down')
    sleep(10)
    net.configLinkStatus('s4','s9','up')
    net.configLinkStatus('s4','s1','down')
    print('s4 - s9 up')
    print('s4 - s5 down')
    sleep(10)
    net.configLinkStatus('s4','s1','up')
    net.configLinkStatus('s4','s5','down')
    print('s4 - s5 up')
    print('s4 - s1 down')
    sleep(10)
    net.configLinkStatus('s4','s5','up')
    print('s4 - s1 up')
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
