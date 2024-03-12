from abc import ABC

from host.host import Host
from network.network_interface import NetworkInterface
from network.packet import Packet
from simulation.clock import Clock
from util.timeout_calculator import TimeoutCalculator

"""
This host follows the SlidingWindow protocol. It maintains a window size and the
list of unACKed packets.
"""


class SlidingWindowHost(Host, ABC):

    def __init__(self, clock: Clock, network_interface: NetworkInterface, window_size: int,
                 timeout_calculator: TimeoutCalculator):
        # Host configuration
        self.timeout_calculator: TimeoutCalculator = timeout_calculator
        self.network_interface: NetworkInterface = network_interface
        self.clock: Clock = clock


        # TODO: Add any stateful information you might need to track the progress of this protocol as packets are
        #  sent and received.
        #    - Feel free to create new variables and classes, just don't delete any existing infrastructure.
        #    - In particular, you should make use of the network interface to interact with the network.
        #    - It's worth keeping in mind that you'll soon have to implement AIMD, which also implements the sliding
        #      window protocol. It might be worth structuring your code here in such a way that you can reuse it for
        #      AIMD.
        self.W = window_size
        self.next_in_order = 0
        self.curr_in_order = 0

        self.inflight = []  # buffer all the packets
        self.timeout_tracker = {}
        self.buffer = []  # keep track of sequence number order


    def run_one_tick(self) -> int | None:
        current_time = self.clock.read_tick()

        # TODO: STEP 1 - Process newly received messages
        #  - These will all be acknowledgement to messages this host has previously sent out.
        #  - You should mark these messages as successfully delivered.
        packets_received = self.network_interface.receive_all()
        for pkt in packets_received:

            if pkt in self.inflight[:]:
                self.timeout_calculator.add_data_point(current_time - pkt.sent_timestamp)
                self.inflight.remove(pkt)  # remove from the list, mark as Ack
                self.curr_in_order += 1  # keep track of max received pkt

                if pkt.sequence_number in [p.sequence_number for p in self.inflight]:
                    self.inflight = [p for p in self.inflight if p.sequence_number != pkt.sequence_number]
                # self.buffer.append(pkt.sequence_number)

                    if pkt.sequence_number not in self.buffer:
                        self.buffer.append(pkt.sequence_number)
                        self.buffer.sort()  # 1, 2, 5, 6 , 8, ... waiting for 3, 4, 7

                    while self.buffer and self.buffer[0] == self.next_in_order:
                        self.next_in_order += 1  # from 3 --> 4
                        self.buffer.pop(0)  # discard prev


        # TODO: STEP 2 - Retry any messages that have timed out
        #  - When you transmit each packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see if there are any inflight messages who's timeout has already passed
        #  - If you find a timed out message, create a new packet and transmit it
        #      - The new packet should have the same sequence number
        #      - You should set the packet's retransmission_flag to true
        #      - The sent time should be the current timestamp
        #      - Use the transmit() function of the network interface to send the packet
        for i, pkt in enumerate(self.inflight[:]):
            if (current_time - pkt.sent_timestamp) >= self.timeout_tracker[pkt.sequence_number]:
                retransmit_pkt = Packet(sent_timestamp=current_time, sequence_number=pkt.sequence_number, retransmission_flag=True, ack_flag=False)
                self.network_interface.transmit(retransmit_pkt)  # retransmit the new packet

                self.inflight.remove(pkt)
                self.inflight.append(retransmit_pkt)

                # set the new timeout for the same seq num
                self.timeout_tracker[retransmit_pkt.sequence_number] = self.timeout_calculator.timeout()


        # TODO: STEP 3 - Transmit new messages
        #  - When you transmit each packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see how many additional packets we can put inflight based on the sliding window spec
        #  - Construct and transmit the packets
        #      - Each new packet represents a new message that should have its own unique sequence number
        #      - Sequence numbers start from 0 and increase by 1 for each new message
        #      - Use the transmit() function of the network interface to send the packet

        # buffered window is not full yet, and still waiting the sequence within the W range
        while len(self.inflight) < self.W:
            new_pkt = Packet(sent_timestamp=current_time, sequence_number=self.next_in_order, ack_flag=False)
            self.network_interface.transmit(new_pkt)
            self.inflight.append(new_pkt)

            # set initial timeout once create it
            self.timeout_tracker[new_pkt.sequence_number] = self.timeout_calculator.timeout()
            self.next_in_order += 1

        # TODO: STEP 4 - Return
        #  - Return the largest in-order sequence number
        #      - That is, the sequence number such that it, and all sequence numbers before, have been ACKed

        return self.curr_in_order - 1
