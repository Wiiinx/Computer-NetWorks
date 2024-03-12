from abc import ABC

from host.host import Host
from network.network_interface import NetworkInterface
from network.packet import Packet
from simulation.clock import Clock
from util.timeout_calculator import TimeoutCalculator

"""
This host implements the stop and wait protocol. Here the host only
sends one packet in return of an acknowledgement.
"""


class StopAndWaitHost(Host, ABC):

    def __init__(self, clock: Clock, network_interface: NetworkInterface, timeout_calculator: TimeoutCalculator):
        # Host configuration
        self.timeout_calculator: TimeoutCalculator = timeout_calculator
        self.network_interface: NetworkInterface = network_interface
        self.clock: Clock = clock

        self.next_in_order = 0  # keep track of the next pkt
        self.curr_in_order = -1  # keep track of highest sequence number been acked pkt
        self.inflight = None

        # TODO: Add any stateful information you might need to track the progress of this protocol as packets are
        #  sent and received.
        #    - Feel free to create new variables and classes, just don't delete any existing infrastructure.
        #    - In particular, you should make use of the network interface to interact with the network.

    def run_one_tick(self) -> int | None:
        current_time = self.clock.read_tick()

        # TODO: STEP 1 - Process newly received messages
        #  - These will all be acknowledgement to messages this host has previously sent out.
        #  - You should mark these messages as successfully delivered.
        packets_received = self.network_interface.receive_all()

        for pkt in packets_received:
            if pkt.sequence_number == self.next_in_order and pkt.ack_flag:
                self.curr_in_order = pkt.sequence_number
                self.next_in_order = self.curr_in_order + 1  # next_in_order number + 1
                # pkt.ack_flag = True  # mark as Acked
                self.inflight = None  # clear all the inflight pkt

        # TODO: STEP 2 - Retry any messages that have timed out
        #  - When you transmit a packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see if the inflight message's timeout has already passed.
        #  - If the packet did time out, construct a new packet and transmit
        #      - The new packet should have the same sequence number
        #      - You should set the packet's retransmission_flag to true
        #      - The sent time should be the current timestamp
        #      - Use the transmit() function of the network interface to send the packet
        if self.inflight and (current_time - self.inflight.sent_timestamp) >= self.timeout_calculator.timeout():
            # create a new packet for retransmission
            retransmit_pkt = Packet(sent_timestamp=current_time, sequence_number=self.inflight.sequence_number, retransmission_flag=True, ack_flag=False)
            self.network_interface.transmit(retransmit_pkt)  # retransmit the new packet
            self.inflight.sent_timestamp = current_time



        # TODO: STEP 3 - Transmit new messages
        #  - When you transmit a packet (in steps 2 and 3), you should track that message as inflight
        #  - If you don't have a message inflight, we should send the next message
        #  - Construct and transmit the packet
        #      - The packet represents a new message that should have its own unique sequence number
        #      - Sequence numbers start from 0 and increase by 1 for each new message
        #      - Use the transmit() function of the network interface to send the packet

        if not self.inflight and self.curr_in_order + 1 == self.next_in_order:
            new_pkt = Packet(sent_timestamp=current_time, sequence_number=self.next_in_order, ack_flag=False)
            self.network_interface.transmit(new_pkt)
            self.inflight = new_pkt

        # TODO: STEP 4 - Return
        #  - Return the largest in-order sequence number
        #      - That is, the sequence number such that it, and all sequence numbers before, have been ACKed

        return self.curr_in_order
