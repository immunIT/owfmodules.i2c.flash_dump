# -*- coding: utf-8 -*-

# Octowire Framework
# Copyright (c) ImmunIT - Jordan Ovrè / Paul Duncan
# License: Apache 2.0
# Paul Duncan / Eresse <pduncan@immunit.ch>
# Jordan Ovrè / Ghecko <jovre@immunit.ch>

from tqdm import tqdm

from octowire_framework.module.AModule import AModule
from octowire.i2c import I2C


class FlashDump(AModule):
    def __init__(self, owf_config):
        super(FlashDump, self).__init__(owf_config)
        self.meta.update({
            'name': 'I2C flash dump',
            'version': '1.1.0',
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
            "start_chunk": {"Value": "", "Required": True, "Type": "int",
                            "Description": "Start chunk address (see chunk_size\nadvanced options)",
                            "Default": 0},
            "i2c_baudrate": {"Value": "", "Required": True, "Type": "int",
                             "Description": "I2C frequency in Hz (supported values: 100000 or 400000)",
                             "Default": 400000},
        }
        self.advanced_options.update({
            "chunk_size": {"Value": "", "Required": True, "Type": "int",
                           "Description": "Flash chunk size (128 bytes page by default)", "Default": 128}
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
        start_chunk_addr = self.options["start_chunk"]["Value"]
        chunk_size = self.advanced_options["chunk_size"]["Value"]
        slave_addr = self.options["slave_address"]["Value"]
        chunks = self.options["chunks"]["Value"]
        dump_file = self.options["dumpfile"]["Value"]
        int_addr_length = self.options["int_addr_length"]["Value"]

        # Flash memory size
        size = chunk_size * chunks

        # Buffer
        buff = bytearray()

        # Setup and configure I2C interface
        i2c_interface = I2C(serial_instance=self.owf_serial, bus_id=bus_id)
        i2c_interface.configure(baudrate=i2c_baudrate)

        self.logger.handle("Starting dump: {}.".format(self._sizeof_fmt(size)), self.logger.HEADER)

        try:
            for chunk_nb in tqdm(range(start_chunk_addr, chunks), desc="Reading",
                                 unit_scale=False, ascii=" #", unit_divisor=1,
                                 bar_format="{desc} : {percentage:3.0f}%[{bar}] {n_fmt}/{total_fmt} chunks "
                                            "(" + str(chunk_size) + " bytes) "
                                            "[elapsed: {elapsed} left: {remaining}]"):
                chunk_addr = chunk_nb * chunk_size
                resp = i2c_interface.receive(size=chunk_size, i2c_addr=slave_addr, int_addr=chunk_addr,
                                             int_addr_length=int_addr_length)
                if not resp:
                    raise Exception("Unexpected error while reading the I2C flash")
                buff.extend(resp)
            self.logger.handle("Successfully dumped {} from flash memory.".format(self._sizeof_fmt(size)),
                               self.logger.SUCCESS)
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
