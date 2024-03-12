from typing import List
from matplotlib import pyplot as plt

from network.network_interface import NetworkInterface
from simulation.clock import Clock
from util.timeout_calculator import TimeoutCalculator
from simulation import simulation_logger as log
from network.packet import Packet

"""
This class implements a host that follows the AIMD protocol.
"""


class AimdHost:

    def __init__(self, clock: Clock, network_interface: NetworkInterface, timeout_calculator: TimeoutCalculator):
        # Host configuration
        self.timeout_calculator: TimeoutCalculator = timeout_calculator
        self.network_interface: NetworkInterface = network_interface
        self.clock: Clock = clock

        # TODO: Add any stateful information you might need to track the progress of this protocol as packets are
        #  sent and received. Your sliding window should be initialized to a size of 1, and should use the slow start
        #  algorithm until you hit your first timeout
        #    - Feel free to create new variables and classes, just don't delete any existing infrastructure.
        #    - In particular, you should make use of the network interface to interact with the network.

        self.next_in_order = 0
        self.curr_in_order = -1
        self.W = 1.0  # initial size of the window
        self.window_size_list = []  # keep track of all the windows

        self.slow_start = True
        self.inflight = []  # buffer all the packets
        self.timeout_tracker = {}  # time out tracker
        self.buffer = []

    def set_window_size(self, new_window_size: float, old_window_size: float):

        if new_window_size < old_window_size:
            log.add_event(type="Shrinking Window", desc=f"Old: {old_window_size}, New: {new_window_size}")
        if old_window_size < new_window_size:
            log.add_event(type="Expanding Window", desc=f"Old: {old_window_size}, New: {new_window_size}")
        # TODO: Update the sliding window
        self.W = new_window_size
        self.window_size_list.append(self.W)


    @staticmethod
    def plot(window_sizes: List[int]):
        plt.plot(window_sizes, label="Window Sizes", color="red", linewidth=2, alpha=0.5)
        plt.ylabel("Window Size")
        plt.xlabel("Tick")
        plt.legend()
        plt.savefig("aimd-window-sizes.png")
        plt.close()

    def shutdown_hook(self):
        # TODO: Save the window sizes over time so that, when the simulation finishes, we can plot them over time.
        #  Then, pass those values in here
        self.plot(self.window_size_list)

    def run_one_tick(self) -> int | None:
        current_time = self.clock.read_tick()

        # TODO: STEP 1 - Process newly received messages
        #  - These will all be acknowledgement to messages this host has previously sent out.
        #  - You should mark these messages as successfully delivered.
        #  - You should also increase the size of the window
        #      - You should start in "slow-start" mode to quickly ramp up to the bandwidth capacity.
        #      - Exit "slow-start" mode once your first timeout occurs
        congestion_detected = False
        packets_received = self.network_interface.receive_all()

        # same from the sliding window question
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

                if self.slow_start:
                    # Increase window size by 1 for each ACK in slow start
                    self.set_window_size(self.W + 1.0, self.W)
                    break
                else:
                    self.set_window_size(self.W + 1.0 / self.W, self.W)  # congestion avoidance

        # TODO: STEP 2 - Retry any messages that have timed out
        #  - When you transmit each packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see if there are any inflight messages who's timeout has already passed
        #  - If you find a timed out message, create a new packet and transmit it
        #      - The new packet should have the same sequence number
        #      - You should set the packet's retransmission_flag to true
        #      - The sent time should be the current timestamp
        #      - Use the transmit() function of the network interface to send the packet
        #  - Shrink the sliding window
        #      - This should happen at most once per RTT
        #      - The window size should not go below 1

        for pkt in self.inflight[:]:
             #  print("pkt num: ", pkt.sequence_number, current_time - pkt.sent_timestamp, self.timeout_tracker[pkt.sequence_number])
            if (current_time - pkt.sent_timestamp) >= self.timeout_tracker[pkt.sequence_number]:
                retransmit_pkt = Packet(sent_timestamp=current_time, sequence_number=pkt.sequence_number, retransmission_flag=True, ack_flag=False)
                self.network_interface.transmit(retransmit_pkt)  # retransmit the new packet
                self.inflight.remove(pkt)
                self.inflight.append(retransmit_pkt)
                self.timeout_tracker[retransmit_pkt.sequence_number] = self.timeout_calculator.timeout()

                #if self.inflight:
                #if (current_time - latest_pkt.sent_timestamp) >= self.timeout_calculator.timeout():
                # retransmit the packet
                #retransmit_pkt = Packet(sent_timestamp=current_time, sequence_number=pkt.sequence_number, retransmission_flag=True, ack_flag=False)
                #self.network_interface.transmit(retransmit_pkt)  # retransmit the new packet

                if self.slow_start:
                    self.slow_start = False
                self.set_window_size(max(self.W / 2, 1), self.W)  # shrink the window

        # TODO: STEP 3 - Transmit new messages
        #  - When you transmit each packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see how many additional packets we can put inflight based on the sliding window spec
        #  - Construct and transmit the packets
        #      - Each new packet represents a new message that should have its own unique sequence number
        #      - Sequence numbers start from 0 and increase by 1 for each new message
        #      - Use the transmit() function of the network interface to send the packet

        # still same from sliding window, sending new pky
        while len(self.inflight) < self.W and self.next_in_order <= self.curr_in_order + self.W:
            new_pkt = Packet(sent_timestamp=current_time, sequence_number=self.next_in_order, ack_flag=False)
            self.network_interface.transmit(new_pkt)
            self.inflight.append(new_pkt)

            # set initial timeout once create it
            self.timeout_tracker[new_pkt.sequence_number] = self.timeout_calculator.timeout()
            self.next_in_order += 1

        # TODO: STEP 4 - Return
        #  - Return the largest in-order sequence number
        #      - That is, the sequence number such that it, and all sequence numbers before, have been ACKed


        return self.curr_in_order
