#!/usr/bin/python3

import sys
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch
from mininet.clean import Cleanup

from customer_topology import Ring, Mesh, Linear, Tree
# competition topology
from customer_topology import Competition_3_1, Competition_4_2, Competition_4_3, Competition_5_2, Competition_6_2

from time import sleep
import time
import argparse
import json
import requests
import collections


def _curl_links(controller_ip='127.0.0.1', method = 'topology'):
    try:
        r = requests.get('http://' + controller_ip + ':9191/' + method)
        d = json.loads(r.content.decode('utf-8'))
        return d
    except requests.ConnectionError:
        print("can't connect")
        Cleanup.cleanup()
        exit()
    except UnboundLocalError:
        print("requests error")  
        Cleanup.cleanup()
        exit()

def runMinimalTopo(topo, switch_size = 25, controller_ip = '127.0.0.1', disconnect_links = {}, detect_ports = {}):
    # Create a network based on the topology using OVS and controlled by
    # a remote controller.
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController( name, ip=controller_ip ),
        switch=OVSSwitch,
        autoSetMacs=True )

    # Actually start the network
    net.start()

    links_count = len(_curl_links(controller_ip)['links'])
    while links_count != topo.link_size and topo.link_size != None:
        sleep(2)
        links_count = len(_curl_links(controller_ip)['links'])

    if disconnect_links != None and len(disconnect_links) != 0:
        h1, h2 = net.get( 'h1', 'h2' )
        print('Start testing failover! current time: ' + time.strftime('%H:%M:%S'))

        h1.cmd('arping -c 1 10.0.0.2')
        h2.cmd('nohup ~/ryu/ryu/competition_topology/server.sh > ~/temp.log &')
        h1.cmd('nohup ~/ryu/ryu/competition_topology/send.sh 10.0.0.2 > /dev/null 2>&1 &')

        pre_time = 0
        for current_time in disconnect_links:
            sleep(int(current_time) - int(pre_time))

            for disconnect_link in disconnect_links[current_time]:
                print(
                    'current time: ' + time.strftime('%H:%M:%S') +
                    ', trigger time: ' + current_time +
                    ', (' + disconnect_link[0] +
                    ',' + disconnect_link[1] +
                    ') => ' + disconnect_link[2] + '!'
                )
                net.configLinkStatus(
                    disconnect_link[0],
                    disconnect_link[1],
                    disconnect_link[2],
                )
            pre_time = current_time

        h1.cmd('kill %nohup')
        h2.cmd('kill %nohup')

    if detect_ports != None and len(detect_ports) != 0:
        h1, h2 = net.get( 'h1', 'h2' )
        print('Start testing packet detect! current time: ' + time.strftime('%H:%M:%S'))

        pre_time = 0
        for current_time in detect_ports:
            sleep(int(current_time) - int(pre_time))

            send_time   = detect_ports[current_time][0]
            bandwidth   = int(detect_ports[current_time][1])
            upbound     = bandwidth + int(bandwidth * 0.1)
            downbound   = bandwidth - int(bandwidth * 0.1)
            dpid        = str(detect_ports[current_time][2])
            port        = str(detect_ports[current_time][3])
            start_time  = time.time()

            print('time: ' + current_time + ' ~ ' + str(int(current_time) + int(send_time)))
            print(
                'current time: ' + time.strftime("%H:%M:%S" , time.localtime(start_time)) + 
                ', send time: ' + send_time +
                ', bandwidth: ' +  str(bandwidth) +
                '(' + str(downbound) +
                ' ~ ' + str(upbound) +
                '), dpid: ' + dpid +
                ', port: ' + port
            )

            if bandwidth != 0:
                h2.cmd('iperf -s -u -D')
                h1.cmd('nohup iperf -c 10.0.0.2 -t ' + send_time + \
                    ' -i 1 -u -b ' + str(bandwidth) + 'K > /dev/null 2>&1 &')

            for step in range(int(send_time)):
                if (int(time.time()) - int(start_time)) >= int(send_time):
                    break
                port_stats = _curl_links(
                                    controller_ip=controller_ip,
                                    method='linkbandwidth?dpid=' + dpid + '&port=' + port
                            )
                base_bandwidth = max(int(port_stats['rx']), int(port_stats['tx']))
                key = u'\u2714' if (base_bandwidth >= downbound) and (base_bandwidth <= upbound) else u'\u2718'

                print(
                    'current time: ' + time.strftime("%H:%M:%S") +
                    ', dpid: ' + dpid +
                    ', port: ' + port +
                    ', tx: ' + str(port_stats['tx']) +
                    ', rx: ' + str(port_stats['rx']) +
                    ' ' + key
                )

            pre_time = int(current_time) + int(send_time)

    # Drop the user in to a CLI so user can run commands.
    CLI( net )

    # After the user exits the CLI, shutdown the network.
    net.stop()

def load_json_file(file_name):
    try:
        file = open(file_name).read()
        content_dict = dict(json.loads(file))
        ordered_dict = collections.OrderedDict(sorted(content_dict.items(), key=lambda k : int(k[0])))
        return ordered_dict
    except TypeError:
        print('file open error!')
    except ValueError:
        print('Json format error!')
    except IOError:
        print('file not found!')
    return None

def parse_input():
    parser = argparse.ArgumentParser(description='generate customer topology.')
    parser.add_argument('--topo', dest="topology_type", default="ring",
        help='topology type, include ring | mesh. (default:ring)')
    parser.add_argument('--controller', dest="controller_ip", default="127.0.0.1",
        help='specific controller ip. (default: 127.0.0.1)')
    parser.add_argument('--size', dest="switch_size", default=25,
        help='specific switch size. (default: 25). if topo is tree representative tree level.')
    parser.add_argument('--disconnect', dest="disconnect_file_name", default=None,
         help='specific file name of disconnect links(json format).')
    parser.add_argument('--detect', dest="detect_file_name", default=None,
         help='specific file name of detect ports(json format).')

    args = parser.parse_args()
    topology_type = args.topology_type
    controller_ip = args.controller_ip
    switch_size = int(args.switch_size)

    disconnect_file_name = args.disconnect_file_name
    disconnect_links = None
    if disconnect_file_name != None:
        disconnect_links = load_json_file(disconnect_file_name)
        print("disconnect: ", disconnect_links)

    detect_file_name = args.detect_file_name
    detect_ports = None
    if detect_file_name != None:
        detect_ports = load_json_file(detect_file_name)
        print("packet detect: ", detect_ports)

    return topology_type, switch_size, controller_ip, disconnect_links, detect_ports


if __name__ == '__main__':
    # Parse user input
    topology_type, switch_size, controller_ip, disconnect_links, detect_ports = parse_input()

    # Create an instance of our topology
    if topology_type == 'ring':
        topo = Ring(switch_size=switch_size)
    elif topology_type == 'mesh':
        topo = Mesh(switch_size=switch_size)
    elif topology_type == 'linear':
        topo = Linear(switch_size=switch_size)
    elif topology_type == 'tree':
        topo = Tree(level=switch_size)
    elif topology_type == 'competition_3_1':
        topo = Competition_3_1()
    elif topology_type == 'competition_4_2':
        topo = Competition_4_2()
    elif topology_type == 'competition_4_3':
        topo = Competition_4_3()
    elif topology_type == 'competition_5_2':
        topo = Competition_5_2()
    elif topology_type == 'competition_6_2':
        topo = Competition_6_2()

    setLogLevel( 'info' )

    # This runs if this file is executed directly
    try:
        runMinimalTopo(topo, switch_size, controller_ip, disconnect_links, detect_ports)
    except:
        Cleanup.cleanup()
        runMinimalTopo(topo, switch_size, controller_ip, disconnect_links, detect_ports)
