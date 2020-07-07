# -*- coding: utf-8 -*-

# Octowire Framework
# Copyright (c) ImmunIT - Jordan Ovrè / Paul Duncan
# License: Apache 2.0
# Paul Duncan / Eresse <pduncan@immunit.ch>
# Jordan Ovrè / Ghecko <jovre@immunit.ch>

import shutil
import time

from octowire_framework.module.AModule import AModule
from octowire.i2c import I2C


class FlashDump(AModule):
    def __init__(self, owf_config):
        super(FlashDump, self).__init__(owf_config)
        self.meta.update({
            'name': 'I2C flash dump',
            'version': '1.0.1',
            'description': 'Dump generic I2C flash memories',
            'author': 'Jordan Ovrè / Ghecko <jovre@immunit.ch>, Paul Duncan / Eresse <pduncan@immunit.ch>'
        })
        self.options = {
            "i2c_bus": {"Value": "", "Required": True, "Type": "int",
                        "Description": "I2C bus (0=I2C0 or 1=I2C1)", "Default": 0},
            "slave_address": {"Value": "", "Required": True, "Type": "hex",
                              "Description": "I2C target chip address", "Default": ""},
            "int_addr_length": {"Value": "", "Required": True, "Type": "int",
                                "Description": "Target chip internal address length (bytes)", "Default": 2},
            "dumpfile": {"Value": "", "Required": True, "Type": "file_w",
                         "Description": "Dump output filename", "Default": ""},
            "chunks": {"Value": "", "Required": True, "Type": "int",
                       "Description": "Number of chunks (see chunk_size\nadvanced options)", "Default": 512},
            "start_chunk": {"Value": "", "Required": True, "Type": "hex",
                            "Description": "Start chunk address (see chunk_size\nadvanced options)",
                            "Default": 0x0000},
            "i2c_baudrate": {"Value": "", "Required": True, "Type": "int",
                             "Description": "I2C frequency in Hz (supported values: 100000 or 400000)",
                             "Default": 400000},
        }
        self.advanced_options.update({
            "chunk_size": {"Value": "", "Required": True, "Type": "hex",
                           "Description": "Flash chunk size (128 byte pages by default)", "Default": 0x80}
        })

    @staticmethod
    def _sizeof_fmt(num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def flash_dump(self):
        bus_id = self.options["i2c_bus"]["Value"]
        i2c_baudrate = self.options["i2c_baudrate"]["Value"]
        current_chunk_addr = self.options["start_chunk"]["Value"]
        chunk_size = self.advanced_options["chunk_size"]["Value"]
        slave_addr = self.options["slave_address"]["Value"]
        chunks = self.options["chunks"]["Value"]
        dump_file = self.options["dumpfile"]["Value"]
        int_addr_length = self.options["int_addr_length"]["Value"]

        # Flash memory size
        size = chunk_size * chunks

        # Get the width of the terminal for dynamic printing
        t_width, _ = shutil.get_terminal_size()

        # Buffer
        buff = bytearray()

        # Setup and configure I2C interface
        i2c_interface = I2C(serial_instance=self.owf_serial, bus_id=bus_id)
        i2c_interface.configure(baudrate=i2c_baudrate)

        self.logger.handle("Starting dump: {}.".format(self._sizeof_fmt(size)), self.logger.HEADER)

        try:
            start_time = time.time()
            while current_chunk_addr < size:
                resp = i2c_interface.receive(size=chunk_size, i2c_addr=slave_addr, int_addr=current_chunk_addr,
                                             int_addr_length=int_addr_length)
                if not resp:
                    raise Exception("Unexpected error while reading the I2C flash")
                buff.extend(resp)
                current_chunk_addr += chunk_size
            self.logger.handle("Successfully dumped {} from flash memory.".format(self._sizeof_fmt(current_chunk_addr)),
                               self.logger.SUCCESS)
            self.logger.handle("Dumped in {} seconds.".format(time.time() - start_time, self.logger.INFO))
            with open(dump_file, 'wb') as f:
                f.write(buff)
            self.logger.handle("Dump saved into {}".format(dump_file), self.logger.RESULT)
        except (Exception, ValueError) as err:
            self.logger.handle(err, self.logger.ERROR)

    def run(self):
        """
        Main function.
        Dump generic I2C flash memories
        :return: Nothing
        """
        # Detect and connect to the Octowire hardware. Set the self.owf_serial variable if found.
        self.connect()
        if not self.owf_serial:
            return
        try:
            self.flash_dump()
        except (Exception, ValueError) as err:
            self.logger.handle(err, self.logger.ERROR)
