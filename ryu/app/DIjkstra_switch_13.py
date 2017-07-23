# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import Dijkstra
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ether_types
from ryu.topology import event,switches
from ryu.topology.api import get_switch, get_link, get_host
from collections import defaultdict
from pprint import pprint

ETHERNET_MULTICAST = 'ff:ff:ff:ff:ff:ff'

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.switch_list = []
        self.hosts_list = []
        self.link_dict = {}
        self.mac_to_port = {}
        self.arp_table = {}
        self.arp_switch_table = {}

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology(self, req, **kwargs):
        switches = get_switch(self, None)
        self.switch_list = [switch.dp.id for switch in switches]

        links = get_link(self,None)
        self.link_dict = { (link.src.dpid, link.dst.dpid) : {
                                'src_port_no' : link.src.port_no, 
                                'weight' : 1
                            } for link in links }
        # pprint(self.switch_list)
        # pprint(self.link_dict)
        # print('src_port_no:',self.link_dict[(2,3)]['src_port_no'])
        # print('weight:',self.link_dict[(2,3)]['weight'])

    def get_hosts(self, req, **kwargs):
        hosts = get_host(self, None)
        self.hosts_list = [ { host.mac : {
                                'dpid' : host.port.dpid,
                                'port_no' : host.port.port_no}
                            } for host in hosts]
        # pprint(self.hosts_list)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def delete_flow(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        for dst in self.mac_to_port[datapath.id].keys():
            match = parser.OFPMatch(eth_dst=dst)
            mod = parser.OFPFlowMod(datapath=datapath, priority=1, match=match,
                                    out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                                    command=ofproto.OFPFC_DELETE)
            datapath.send_msg(mod)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        src = eth.src
        dst = eth.dst

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            pkt_arp = pkt.get_protocols(arp.arp)[0]
            self.arp_table[pkt_arp.src_ip] = src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port
        self.logger.info("packet type [%s] in %s %s %s %s", eth.ethertype, dpid, src, dst, in_port)

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        elif eth.ethertype == ether_types.ETH_TYPE_ARP \
        and self.arp_proxy(eth, pkt_arp, datapath, in_port, msg.buffer_id):
            print("☞ APR_PROXY ☚")
            return None
        else:
            out_port = ofproto.OFPP_FLOOD
            print("☠ OFPP_FLOOD ☠")

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return None
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def arp_proxy(self, eth, pkt_arp, datapath, in_port, msg_buffer_id):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        arp_src_ip = pkt_arp.src_ip
        arp_dst_ip = pkt_arp.dst_ip
        eth_dst = eth.dst
        eth_src = eth.src
        
        if eth_dst == ETHERNET_MULTICAST:
            if self.arp_switch_table.setdefault(
            (datapath.id, eth_src, arp_dst_ip), in_port) != in_port:
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                          in_port=in_port, actions=[], data=None)
                datapath.send_msg(out)
                return True

        if pkt_arp.opcode == arp.ARP_REQUEST:
            if arp_dst_ip in self.arp_table:    # arp reply
                ARP_Reply = packet.Packet()
                ARP_Reply.add_protocol(ethernet.ethernet(
                    ethertype=eth.ethertype, dst=eth_src, 
                    src=self.arp_table[arp_dst_ip]))
                ARP_Reply.add_protocol(arp.arp(
                    opcode=arp.ARP_REPLY, src_mac=self.arp_table[arp_dst_ip], 
                    src_ip=arp_dst_ip, dst_mac=eth_src, dst_ip=arp_src_ip))
                ARP_Reply.serialize()

                actions = [parser.OFPActionOutput(in_port)]
                out = parser.OFPPacketOut(
                        datapath=datapath,
                        buffer_id=ofproto.OFP_NO_BUFFER,
                        in_port=ofproto.OFPP_CONTROLLER,
                        actions=actions, data=ARP_Reply.data)
                datapath.send_msg(out)
                return True
        return False