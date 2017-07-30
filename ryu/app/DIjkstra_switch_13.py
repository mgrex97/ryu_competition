# coding=utf-8
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
from ryu.topology import event
from ryu.topology.api import get_switch, get_link, get_host
from collections import defaultdict
from pprint import pprint

ETHERNET_MULTICAST = 'ff:ff:ff:ff:ff:ff'

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.switch_list = []                   # Init in get_topology()
        self.switchs_datapath = {}              # Init in get_topology()
        self.link_dict = {}                     # Init in get_topology()
        self.hosts_list = {}                    # Init in get_hosts()
        self.arp_table = {}
        self.arp_switch_table = {}
        self.Dijkstra_Graph = Dijkstra.Graph()  # Init in get_topology()

    @set_ev_cls(event.EventSwitchEnter)
    def Switch_Enter(self, req):
        print("Switch_Enter")
        self.Dijkstra_Graph = Dijkstra.Graph()
        # self._get_switchs()

    @set_ev_cls(event.EventSwitchLeave)
    def Switch_Leave(self, req):
        print("Switch_Leave")
        self.Dijkstra_Graph = Dijkstra.Graph()
        # self._get_switchs()

    @set_ev_cls(event.EventLinkAdd)
    def Link_Add(self, req):
        print("Link_Add")
        self.Dijkstra_Graph = Dijkstra.Graph()
        # self._get_link()

    @set_ev_cls(event.EventLinkDelete)
    def Link_Delete(self, req):
        print("Link_Delete")
        self.Dijkstra_Graph = Dijkstra.Graph()
        # self._get_link()

    def _init_switchs(self):
        switches = get_switch(self, None)
        hosts = get_host(self, None)
        # Init Switch
        for switch in switches :
            for host in hosts :
                self.delete_flow(switch.dp, host.mac)

    def _get_switchs(self):
        switches = get_switch(self, None)

        self.switch_list = [switch.dp.id for switch in switches]
        self.switchs_datapath = {switch.dp.id : switch.dp for switch in switches}

        # Set Dijkstra nodes
        self.Dijkstra_Graph.set_node(self.switch_list)

    def _get_link(self):
        links = get_link(self,None)
    
        self.link_dict = { 
            (link.src.dpid, link.dst.dpid) : {
               'port_no' : link.src.port_no
            } for link in links }

        # Set Dijkstra edges
        for link in links :
            self.Dijkstra_Graph.add_edge(link.src.dpid, link.dst.dpid, 1)

    def _get_topo(self):
        self.arp_table = {}
        self.arp_switch_table = {}
        self.Dijkstra_Graph = Dijkstra.Graph()
        self._init_switchs()
        self._get_switchs()
        self._get_link()

    @set_ev_cls(event.EventHostAdd)
    def get_hosts(self, req):
        print("EventHostAdd")
        hosts = get_host(self, None)
        self.hosts_list = {
            host.mac : {
                'dpid' : host.port.dpid,
                'port_no' : host.port.port_no
            } for host in hosts }
        # hosts_node = [host.port.dpid for host in hosts]
        # while len(hosts_node) > 1 :
            # Dijkstra.dijsktra(self.Dijkstra_Graph, hosts_node.pop(), hosts_node)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def delete_flow(self, datapath, dst):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

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

    def add_Dijkstra_path_flow(self, src_dpid, dst_dpid, src, dst):
        Dijkstra_path = Dijkstra.dijsktra(self.Dijkstra_Graph, src_dpid, dst_dpid)
        while Dijkstra_path == None :
            print("\u2620 Dijkstra_ERROR \u2620")
            self._get_topo()
            Dijkstra_path = Dijkstra.dijsktra(self.Dijkstra_Graph, src_dpid, dst_dpid)
        # print("Dijkstra_path:",Dijkstra_path)
        if len(Dijkstra_path) > 1:
            prev_dpid = src_dpid
            for index, dpid in enumerate(Dijkstra_path[:-1]) :
                next_dpid = Dijkstra_path[index + 1]
                # print("prev_dpid:", prev_dpid, "dpid:", dpid, "next_dpid:", next_dpid)
                datapath = self.switchs_datapath[dpid]
                in_port  = self.link_dict[(dpid, prev_dpid)]['port_no']
                out_port = self.link_dict[(dpid, next_dpid)]['port_no']
                # print("in_port:", in_port, "out_port:", out_port)
                parser = datapath.ofproto_parser
                match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
                actions = [parser.OFPActionOutput(out_port)]
                self.add_flow(datapath, 1, match, actions)
                prev_dpid = dpid
        return Dijkstra_path
        
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

        src_dpid = datapath.id
        if dst != ETHERNET_MULTICAST :
            self.logger.info("packet type [%s] in %s %s %s %s", eth.ethertype, src_dpid, src, dst, in_port)
            if dst in self.hosts_list :
                dst_dpid = self.hosts_list[dst]['dpid']
                if src_dpid == dst_dpid:
                    out_port = self.hosts_list[dst]['port_no']
                    # print("End out_port:", out_port)
                else:
                    # print("---Dijkstra Start---")
                    # print("src_dpid:",src_dpid, "dst_dpid",dst_dpid)
                    next_dpid = self.add_Dijkstra_path_flow(src_dpid, dst_dpid, src, dst)[0]
                    out_port = self.link_dict[(src_dpid, next_dpid)]['port_no']
                    # print("next_dpid:", next_dpid, "out_port:", out_port)
                    # print("---Dijkstra End---")
            else:
                print("\u2620 NOT_MATCH \u2620")
                return None
        elif eth.ethertype == ether_types.ETH_TYPE_ARP :
            pkt_arp = pkt.get_protocols(arp.arp)[0]
            self.arp_table[pkt_arp.src_ip] = src
            if self.arp_proxy(eth, pkt_arp, datapath, in_port, msg) :
                print("\u261e APR_PROXY \u261a")
                return None
        else:
            print("\u2620 NOT_MATCH \u2620")
            return None


        if out_port == None : return None
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

    def arp_proxy(self, eth, pkt_arp, datapath, in_port, msg):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        arp_src_ip = pkt_arp.src_ip
        arp_dst_ip = pkt_arp.dst_ip
        eth_dst = eth.dst
        eth_src = eth.src
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        
        if eth_dst == ETHERNET_MULTICAST:
            if self.arp_switch_table.setdefault(
            (datapath.id, eth_src, arp_dst_ip), in_port) != in_port:
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                          in_port=in_port, actions=[], data=data)
                datapath.send_msg(out)
                return True
            else:
                out_port = ofproto.OFPP_FLOOD
                actions = [parser.OFPActionOutput(out_port)]
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)
                print("\u2620 ARP_FLOOD \u2620")
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