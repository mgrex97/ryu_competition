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

import time
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto.ether import ETH_TYPE_IPV6, ETH_TYPE_LLDP, ETH_TYPE_ARP
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

class BestPerformance(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        self.switchs_datapath = {}
        super(BestPerformance, self).__init__(*args, **kwargs)
        self.arp_table = {}
        self.arp_switch_table = {}
        # Saving switch port relevant to which link.
        self.switch_to_link = {}        # {
                                        #    dpid : {
                                        #        port_no: link,
                                        #        ...
                                        #    },...
                                        # }
        # Which and how many hosts connect to the Switch.
        self.switch_to_host = {}        # {
                                        #   dpid : [host_mac,...],...
                                        # }
        self.Dijkstra_Graph = Dijkstra.Graph()  # Init in get_topology()
        # Saving the dpid list which the path going through.
        self.path_sets = {}             #
                                        # {
                                        #    path(src_mac,dest_mac) : [dpid,...],
                                        #    ...
                                        # }
        # host connect to which switch and which port
        self.hosts_list = {}            # {
                                        #    host mac : {
                                        #       'dpid' : dpid,
                                        #       'port_no' : port_no,
                                        #    },...
                                        # }
        # Recod the link will affect which paths.
        self.link_dict = {}             # {
                                        #     link(src,dest) : {
                                        #         'port_no' : port_no,
                                        #         'path_list' : [(src_mac, dest_mac),...] 
                                        #     },...
                                        # }

    @set_ev_cls(event.EventLinkAdd)
    def Link_Add(self, event):
        # Saving new link data.
        link = event.link

        link_condition = (link.src.dpid, link.dst.dpid)

        self.link_dict[link_condition] = {
            'port_no' : link.src.port_no,
            'path_list' : []
        }

        self.switch_to_link[link.src.dpid][link.src.port_no] = link

        # Set Dijkstra edges
        self.Dijkstra_Graph.add_edge(link.src.dpid, link.dst.dpid, 1)

    def Link_Delete(self, link, state = True):
        # Delete the flows of paths, if some paths go through this link.
        link_condition = (link.src.dpid, link.dst.dpid)
        self.Dijkstra_Graph.del_edge(link.src.dpid, link.dst.dpid)

        # This path which is been deleted now will affect exist paths.
        if link_condition in self.link_dict:
            for path_condition  in self.link_dict[link_condition]['path_list']:
                # get host mac
                src_mac = path_condition[0]
                dst_mac = path_condition[1]
                if src_mac not in self.hosts_list \
                or dst_mac not in self.hosts_list:
                    continue
                src_dpid = self.hosts_list[src_mac]['dpid']
                dst_dpid = self.hosts_list[dst_mac]['dpid']
                if path_condition in self.path_sets:
                    # reached_break_point = True
                    # Delete the flow which is relevant to the path.
                    for dpid in self.path_sets[path_condition][:-1]:
                        # if dp_id is not break_point and reached_break_point:
                        # if dpid in self.switchs_datapath and state == True:
                        self.delete_flow(self.switchs_datapath[dpid], dst_mac)
                        # reached_break_point = False
                    del self.path_sets[path_condition]
                    
                    # add_Dijkstra_path_flow(src_dpid,dst_dpid,src_mac,dst_mac)
            del self.link_dict[link_condition]


    @set_ev_cls(event.EventHostAdd)
    def hosts_up(self, event):
        # Save new host data.
        host = event.host
        dpid = int(host.port.dpid)
        switch_port = int(host.port.port_no)

        self.hosts_list[host.mac] = {
            'dpid' : dpid,
            'port_no' : switch_port
        }
        self.switch_to_host[dpid][switch_port] = host.mac


    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        # Check port modify will affect which link or host.
        msg = ev.msg
        dpid = msg.datapath.id
        reason = msg.reason
        port_no = msg.desc.port_no
        ofproto = msg.datapath.ofproto

        if ofproto.OFPP_CONTROLLER == port_no:
            self.logger.info("port controller %s", port_no)
            return

        if reason == ofproto.OFPPR_ADD:
            pass
        elif reason in (ofproto.OFPPR_MODIFY, ofproto.OFPPR_DELETE):
            # Check port have link or not.
            if dpid in self.switch_to_link and port_no in self.switch_to_link[dpid]:
                link = self.switch_to_link[dpid][port_no]
                self.Link_Delete(link, True)
                del self.switch_to_link[dpid][port_no]
            # Check port have host or not.
            elif dpid in self.switch_to_host and port_no in self.switch_to_host[dpid]:
                host_mac = self.switch_to_host[dpid][port_no]
                self.delete_flow(self.switchs_datapath[dpid], host_mac)
                del self.switch_to_host[dpid][port_no]
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)


    # Handle the siwtch disconnect.
    @set_ev_cls(ofp_event.EventOFPStateChange, DEAD_DISPATCHER)
    def Switch_Disconnect(self, event):
        # When switch disconnect, clear the relevant data.
        dp_id = event.datapath.id

        if dp_id in self.switchs_datapath:
            # clear host data which is connect to this switch.
            for port_no, host_mac in self.switch_to_host[dp_id].items():
                self.hosts_list.pop(host_mac, None)

            if dp_id in self.switch_to_link:
                for port_no, link in self.switch_to_link[dp_id].items():
                    self.Link_Delete(link, False)

            self.switch_to_host.pop(dp_id, None)
            self.switch_to_link.pop(dp_id, None)
            self.switchs_datapath.pop(dp_id, None)
            self.Dijkstra_Graph.del_node(dp_id)
            self.arp_table = {}
            self.arp_switch_table = {}

    # Handle the switch connect.
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.switchs_datapath[datapath.id] = datapath
        self.switch_to_host[datapath.id] = {}
        self.switch_to_link[datapath.id] = {}
        self.Dijkstra_Graph.add_node(datapath.id)
        
        self.add_flow(datapath, 0, match, actions)
    
    # Delete specific flow in the ofp switch.
    def delete_flow(self, datapath, dst = None, table_id = 0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        if dst is not None:
            match = parser.OFPMatch(eth_dst=dst)
        else:
            match = parser.OFPMatch()
        mod = parser.OFPFlowMod(datapath=datapath, priority=1, match=match,
                                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                                command=ofproto.OFPFC_DELETE, table_id = table_id)
        datapath.send_msg(mod)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, table_id = 0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst, table_id=table_id)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst, table_id=table_id)
        datapath.send_msg(mod)

    def add_Dijkstra_path_flow(self, src_dpid, dst_dpid, src_mac, dst_mac, src_in_port):
        # Caculate the path then send flows.
        path_condition = (src_mac, dst_mac)
        if path_condition in self.path_sets:
            return None

        Dijkstra_path = Dijkstra.dijsktra(self.Dijkstra_Graph, src_dpid, dst_dpid)
        # Can't find any path.
        if Dijkstra_path == None :
            return None

        self.path_sets[path_condition] = []

        if len(Dijkstra_path) > 1:
            prev_dpid = src_dpid
            for index, dpid in enumerate(Dijkstra_path[:-1]) :
                next_dpid = Dijkstra_path[index + 1]

                datapath = self.switchs_datapath[dpid]
                if src_dpid != dpid:
                    in_port  = self.link_dict[(dpid, prev_dpid)]['port_no']
                out_port = self.link_dict[(dpid, next_dpid)]['port_no']
                parser = datapath.ofproto_parser

                if src_dpid != dpid:
                    match = parser.OFPMatch(in_port = in_port, eth_dst = dst_mac)
                else:
                    match = parser.OFPMatch(in_port = src_in_port, eth_dst = dst_mac)
                actions = [parser.OFPActionOutput(out_port)]

                # Record table_ids of the Path.
                self.path_sets[path_condition].append(datapath.id)

                # Recod link which will affect by the path.
                self.link_dict[(dpid,next_dpid)]['path_list'].append(path_condition)

                self.add_flow(datapath, 1, match, actions)

                prev_dpid = dpid
            self.path_sets[path_condition].append(Dijkstra_path[-1])
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
        src_mac = eth.src
        dst_mac = eth.dst
        out_port = None

        if eth.ethertype in (ETH_TYPE_LLDP ,ETH_TYPE_IPV6):
            # ignore lldp and IPV6 packet
            return            

        src_dpid = datapath.id
        if dst_mac != ETHERNET_MULTICAST:
            if dst_mac in self.hosts_list:
                dst_dpid = self.hosts_list[dst_mac]['dpid']

                if src_dpid == dst_dpid:
                    out_port = self.hosts_list[dst_mac]['port_no']
                else:
                    self.add_Dijkstra_path_flow(src_dpid, dst_dpid, src_mac, dst_mac, in_port)
                    return None
            else:
                # dst not in host_list means host not exist.
                return None
        elif eth.ethertype == ETH_TYPE_ARP :
            pkt_arp = pkt.get_protocols(arp.arp)[0]
            self.arp_table[pkt_arp.src_ip] = src_mac
            # arp proxy
            if self.arp_proxy(eth, pkt_arp, datapath, in_port, msg) :
                return None
        else:
            return None

        if out_port == None : return None
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst_mac)
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
                # ARP_FLOOD
                out_port = ofproto.OFPP_FLOOD
                actions = [parser.OFPActionOutput(out_port)]
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
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
