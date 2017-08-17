#!/usr/bin/python3

import sys
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch
from mininet.clean import Cleanup

from customer_topology import Ring, Full_Mesh, Mesh

from time import sleep
import argparse
import json
import requests
import collections


def _curl_links(controller_ip='127.0.0.1'):
    try:
        r = requests.get('http://' + controller_ip + ':9191/topology')
        d = json.loads(r.content.decode('utf-8'))
        return d['links']
    except requests.ConnectionError:
        print("can't connect")
        Cleanup.cleanup()
        exit()
    except UnboundLocalError:
        print("requests error")  
        Cleanup.cleanup()
        exit()

def runMinimalTopo(topo, switch_size = 25, controller_ip = '127.0.0.1', disconnect_links = {}):
    # Create a network based on the topology using OVS and controlled by
    # a remote controller.
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController( name, ip=controller_ip ),
        switch=OVSSwitch,
        autoSetMacs=True )

    # Actually start the network
    net.start()

    Links_Count = len(_curl_links(controller_ip))
    while Links_Count != topo.link_size and topo.link_size != None:
        sleep(2)
        Links_Count = len(_curl_links(controller_ip))
    print('start testing failover')

    h1, h2 = net.get( 'h1', 'h2' )
    if disconnect_links != None and len(disconnect_links) != 0:
        h1.cmd('arping -c 1 10.0.0.2')
        h2.cmd('nohup ~/ryu/ryu/competition_topology/server.sh > ~/temp.log &')
        h1.cmd('nohup ~/ryu/ryu/competition_topology/send.sh 10.0.0.2 > /dev/null 2>&1 &')

        pre_time = 0
        
        for current_time in disconnect_links:
            sleep(int(current_time) - int(pre_time))

            for disconnect_link in disconnect_links[current_time]:
                print("current time: ", current_time, "disconnect link: ", disconnect_link)
                net.configLinkStatus(
                    disconnect_link[0],
                    disconnect_link[1],
                    disconnect_link[2],
                )
            pre_time = current_time

        h1.cmd('kill %nohup')
        h2.cmd('kill %nohup')

    # Drop the user in to a CLI so user can run commands.
    CLI( net )

    # After the user exits the CLI, shutdown the network.
    net.stop()

def parse_input():
    parser = argparse.ArgumentParser(description='generate customer topology.')
    parser.add_argument('-t', dest="topology_type", default="ring",
        help='topology type, include ring | mesh. (default:ring)')
    parser.add_argument('-i', dest="controller_ip", default="127.0.0.1",
        help='specific controller ip. (default: 127.0.0.1)')
    parser.add_argument('-s', dest="switch_size", default=25,
        help='specific switch size. (default: 25)')
    parser.add_argument('-d', dest="disconnect_file_name", default=None,
         help='specific file name of disconnect links(json format).')

    args = parser.parse_args()
    topology_type = args.topology_type
    controller_ip = args.controller_ip
    switch_size = args.switch_size
    disconnect_file_name = args.disconnect_file_name
    disconnect_links = None

    if disconnect_file_name != None:
        try:
            disconnect_file = open(disconnect_file_name).read()
            disconnect_links = dict(json.loads(disconnect_file))
            disconnect_links = collections.OrderedDict(sorted(disconnect_links.items(), key=lambda k : int(k[0])))
        except TypeError:
            print('file open error!')
        except ValueError:
            print('Json format error!')
        except IOError:
            print('file not found!')

        print(disconnect_links)

    return topology_type, switch_size, controller_ip, disconnect_links


if __name__ == '__main__':
    # Parse user input
    topology_type, switch_size, controller_ip, disconnect_links = parse_input()

    # Create an instance of our topology
    if topology_type == 'ring':
        topo = Ring(switch_size=switch_size)
    elif topology_type == 'mix_mesh':
        topo = Full_Mesh(switch_size=switch_size)
    elif topology_type == 'mesh':
        topo = Mesh()

    setLogLevel( 'info' )

    # This runs if this file is executed directly
    try:
        runMinimalTopo(topo, switch_size, controller_ip, disconnect_links)
    except:
        Cleanup.cleanup()
        runMinimalTopo(topo, switch_size, controller_ip, disconnect_links)