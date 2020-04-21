# -*- coding:utf-8 -*-

# Octowire Framework
# Copyright (c) Jordan Ovrè / Paul Duncan
# License: GPLv3
# Paul Duncan / Eresse <eresse@dooba.io>
# Jordan Ovrè / Ghecko <ghecko78@gmail.com

import shutil
import time

from octowire_framework.module.AModule import AModule
from octowire.i2c import I2C


class FlashDump(AModule):
    def __init__(self, owf_config):
        super(FlashDump, self).__init__(owf_config)
        self.meta.update({
            'name': 'I2C dump flash',
            'version': '1.0.0',
            'description': 'Dump I2C flash memory',
            'author': 'Jordan Ovrè <ghecko78@gmail.com> / Paul Duncan <eresse@dooba.io>'
        })
        self.options = [
            {"Name": "i2c_bus", "Value": "", "Required": True, "Type": "int",
             "Description": "The octowire I2C device (0=I2C0 or 1=I2C1)", "Default": 0},
            {"Name": "slave_address", "Value": "", "Required": True, "Type": "hex",
             "Description": "The I2C target chip address", "Default": ""},
            {"Name": "int_addr_length", "Value": "", "Required": True, "Type": "int",
             "Description": "The internal chip address length (byte)", "Default": 2},
            {"Name": "dumpfile", "Value": "", "Required": True, "Type": "file_w",
             "Description": "The dump filename", "Default": ""},
            {"Name": "chunks", "Value": "", "Required": True, "Type": "int",
             "Description": "The number of chunks (see chunk_size\nadvanced options)", "Default": 512},
            {"Name": "start_chunk", "Value": "", "Required": True, "Type": "hex",
             "Description": "The starting chunk address (see chunk_size\nadvanced options)", "Default": 0x0000},
            {"Name": "i2c_baudrate", "Value": "", "Required": True, "Type": "int",
             "Description": "set I2C baudrate in Hz (supported value: 100000 or 400000)", "Default": 400000},
        ]
        self.advanced_options.append(
            {"Name": "chunk_size", "Value": "", "Required": True, "Type": "hex",
             "Description": "Flash chunk size (128 bytes page by default)", "Default": 0x80}
        )

    @staticmethod
    def _sizeof_fmt(num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def flash_dump(self):
        bus_id = self.get_option_value("i2c_bus")
        i2c_baudrate = self.get_option_value("i2c_baudrate")
        current_chunk_addr = self.get_option_value("start_chunk")
        chunk_size = self.get_advanced_option_value("chunk_size")
        slave_addr = self.get_option_value("slave_address")
        chunks = self.get_option_value("chunks")
        dump_file = self.get_option_value("dumpfile")
        int_addr_length = self.get_option_value("int_addr_length")

        # Flash memory size
        size = chunk_size * chunks

        # Get the size width of the terminal for dynamic printing
        t_width, _ = shutil.get_terminal_size()

        # Buffer
        buff = bytearray()

        # Set and configure I2C interface
        i2c_interface = I2C(serial_instance=self.owf_serial, bus_id=bus_id)
        i2c_interface.configure(baudrate=i2c_baudrate)

        self.logger.handle("Start dumping {}.".format(self._sizeof_fmt(size)), self.logger.HEADER)

        try:
            start_time = time.time()
            while current_chunk_addr < size:
                resp = i2c_interface.receive(size=chunk_size, i2c_addr=slave_addr, int_addr=current_chunk_addr,
                                             int_addr_length=int_addr_length)
                if not resp:
                    raise Exception("Unexpected error while reading the I2C flash")
                buff.extend(resp)
                print(" " * t_width, end="\r", flush=True)
                print("Read: {}".format(self._sizeof_fmt(current_chunk_addr)), end="\r", flush=True)
                current_chunk_addr += chunk_size
            self.logger.handle("Successfully dump {} from flash memory.".format(self._sizeof_fmt(current_chunk_addr)),
                               self.logger.SUCCESS)
            self.logger.handle("Dumped in {} seconds.".format(time.time() - start_time, self.logger.INFO))
            with open(dump_file, 'wb') as f:
                f.write(buff)
            self.logger.handle("Dump saved into {}".format(dump_file), self.logger.RESULT)
        except (Exception, ValueError) as err:
            self.logger.handle(err, self.logger.ERROR)

    def run(self):
        """
        Our code here
        :return:
        """
        # Detect and connect to the octowire hardware. Set the self.owf_serial variable if found.
        self.connect()
        if not self.owf_serial:
            return
        try:
            self.flash_dump()
        except (Exception, ValueError) as err:
            self.logger.handle(err, self.logger.ERROR)
