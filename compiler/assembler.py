#!/usr/bin/env python3
"""
RTCore-V1 Assembler
Assembles RTCore-V1 assembly code to binary
"""

import re
import struct
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Instruction:
    """Assembled instruction"""
    address: int
    opcode: int
    binary: int
    source: str


class RTCoreAssembler:
    """
    Assembler for RTCore-V1 architecture
    Converts assembly to binary machine code
    """

    def __init__(self):
        self.labels = {}
        self.instructions = []
        self.data = bytearray()
        self.current_address = 0x1000  # Code starts at 0x1000
        self.data_address = 0x10000     # Data starts at 0x10000

        # Opcode mapping
        self.opcodes = {
            # Vector operations
            'vadd': 0x01, 'vsub': 0x02, 'vmul': 0x03, 'vdot': 0x04,
            'vcross': 0x05, 'vnorm': 0x06, 'vlength': 0x07, 'vfma': 0x08,
            'vset': 0x09, 'vget': 0x0A, 'vput': 0x0B, 'vsqr': 0x0C,

            # Scalar FP
            'fadd': 0x10, 'fsub': 0x11, 'fmul': 0x12, 'fdiv': 0x13,
            'fsqrt': 0x14, 'fabs': 0x15, 'fneg': 0x16, 'fmin': 0x17,
            'fmax': 0x18, 'ffma': 0x19, 'fmadd': 0x1A, 'fmsub': 0x1B,

            # Integer
            'add': 0x20, 'sub': 0x21, 'mul': 0x22, 'div': 0x23,
            'and': 0x24, 'or': 0x25, 'xor': 0x26, 'slt': 0x27,
            'addi': 0x28,

            # Memory
            'lw': 0x30, 'sw': 0x31, 'lf': 0x32, 'sf': 0x33,
            'lv': 0x34, 'sv': 0x35, 'li': 0x36, 'lif': 0x37,
            'la': 0x38,  # Load address (pseudo-instruction)

            # Control flow
            'beq': 0x40, 'bne': 0x41, 'blt': 0x42, 'bge': 0x43,
            'fbeq': 0x44, 'fbne': 0x45, 'fblt': 0x46, 'fbge': 0x47,
            'jump': 0x48, 'jal': 0x49, 'jalr': 0x4A, 'ret': 0x4B,

            # System/IO
            'readf': 0x50, 'readi': 0x51, 'writeb': 0x52, 'writei': 0x53,
            'halt': 0x5F,
        }

        # Register name mapping
        self.int_regs = {f'r{i}': i for i in range(32)}
        self.float_regs = {f'f{i}': i for i in range(32)}
        self.vector_regs = {f'v{i}': i for i in range(16)}

    def assemble(self, input_file: str, output_file: str):
        """Assemble file to binary"""
        print(f"Assembling {input_file}...")

        # Read source
        with open(input_file, 'r') as f:
            source = f.read()

        # Two-pass assembly
        self.first_pass(source)
        self.second_pass(source)

        # Write binary
        self.write_binary(output_file)

        print(f"Generated {len(self.instructions)} instructions")
        print(f"Code size: {len(self.instructions) * 4} bytes")

    def first_pass(self, source: str):
        """First pass: collect labels"""
        address = self.current_address
        in_data = False

        for line in source.split('\n'):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Check for section directives
            if line.startswith('.'):
                if line == '.data':
                    in_data = True
                    address = self.data_address
                elif line == '.text':
                    in_data = False
                    address = self.current_address
                elif line == '.bss':
                    in_data = True
                continue

            # Check for labels
            if ':' in line and not any(op in line for op in self.opcodes):
                label = line.split(':')[0].strip()
                self.labels[label] = address
                continue

            # Count instructions
            if not in_data:
                address += 4

    def second_pass(self, source: str):
        """Second pass: generate machine code"""
        address = self.current_address
        in_data = False

        for line_num, line in enumerate(source.split('\n'), 1):
            original_line = line
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Handle directives
            if line.startswith('.'):
                if line == '.data':
                    in_data = True
                    address = self.data_address
                elif line == '.text':
                    in_data = False
                    address = self.current_address
                continue

            # Skip labels
            if ':' in line and not any(op in line for op in self.opcodes):
                # Extract instruction after label if present
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    line = parts[1].strip()
                else:
                    continue

            # Assemble instruction
            if not in_data:
                try:
                    instr = self.assemble_instruction(line, address)
                    if instr:
                        self.instructions.append(instr)
                        address += 4
                except Exception as e:
                    print(f"Error on line {line_num}: {original_line}")
                    print(f"  {e}")

    def assemble_instruction(self, line: str, address: int) -> Instruction:
        """Assemble a single instruction"""
        # Parse instruction
        parts = re.split(r'[,\s]+', line)
        mnemonic = parts[0].lower()

        if mnemonic not in self.opcodes:
            return None

        opcode = self.opcodes[mnemonic]

        # Encode based on instruction type
        if mnemonic in ['vadd', 'vsub', 'vmul', 'vdot', 'vcross', 'vnorm', 'vsqr']:
            # Vector R-type: vop vd, va, vb
            binary = self.encode_vector_r(opcode, parts[1:])
        elif mnemonic in ['fadd', 'fsub', 'fmul', 'fdiv', 'fsqrt', 'fabs', 'fneg']:
            # Float R-type: fop fd, fa, fb
            binary = self.encode_float_r(opcode, parts[1:])
        elif mnemonic in ['add', 'sub', 'mul', 'and', 'or', 'xor', 'slt']:
            # Integer R-type
            binary = self.encode_int_r(opcode, parts[1:])
        elif mnemonic in ['addi', 'li']:
            # I-type
            binary = self.encode_i(opcode, parts[1:])
        elif mnemonic in ['lf', 'sf', 'lv', 'sv', 'lw', 'sw']:
            # Memory I-type: lf fd, offset(ra)
            binary = self.encode_memory_i(opcode, parts[1:])
        elif mnemonic in ['beq', 'bne', 'blt', 'bge', 'fbeq', 'fbne', 'fblt', 'fbge']:
            # Branch I-type: beq ra, rb, label
            binary = self.encode_branch(opcode, parts[1:], address)
        elif mnemonic == 'jal':
            # Jump and link
            binary = self.encode_jal(opcode, parts[1:], address)
        elif mnemonic == 'jump':
            # Jump
            binary = self.encode_jump(opcode, parts[1:], address)
        elif mnemonic == 'ret':
            # Return (jalr r0, r1)
            binary = self.encode_r(0x4A, [0, 1, 0])
        elif mnemonic == 'halt':
            # Halt
            binary = (opcode << 26)
        elif mnemonic == 'la':
            # Load address (pseudo-instruction)
            # Expands to: li rd, addr
            binary = self.encode_load_address(parts[1:])
        else:
            # Default R-type encoding
            binary = self.encode_r(opcode, parts[1:])

        return Instruction(address, opcode, binary, line)

    def encode_r(self, opcode: int, operands: List[str]) -> int:
        """Encode R-type instruction"""
        # Format: [6-bit opcode][5-bit rd][5-bit rs1][5-bit rs2][11-bit funct]
        rd = self.parse_register(operands[0]) if len(operands) > 0 else 0
        rs1 = self.parse_register(operands[1]) if len(operands) > 1 else 0
        rs2 = self.parse_register(operands[2]) if len(operands) > 2 else 0

        binary = (opcode << 26) | (rd << 21) | (rs1 << 16) | (rs2 << 11)
        return binary

    def encode_vector_r(self, opcode: int, operands: List[str]) -> int:
        """Encode vector R-type instruction"""
        vd = self.vector_regs.get(operands[0], 0)
        va = self.vector_regs.get(operands[1], 0) if len(operands) > 1 else 0
        vb_or_fs = 0

        if len(operands) > 2:
            if operands[2] in self.vector_regs:
                vb_or_fs = self.vector_regs[operands[2]]
            elif operands[2] in self.float_regs:
                vb_or_fs = self.float_regs[operands[2]]

        binary = (opcode << 26) | (vd << 21) | (va << 16) | (vb_or_fs << 11)
        return binary

    def encode_float_r(self, opcode: int, operands: List[str]) -> int:
        """Encode float R-type instruction"""
        fd = self.float_regs.get(operands[0], 0)
        fa = self.float_regs.get(operands[1], 0) if len(operands) > 1 else 0
        fb = self.float_regs.get(operands[2], 0) if len(operands) > 2 else 0

        binary = (opcode << 26) | (fd << 21) | (fa << 16) | (fb << 11)
        return binary

    def encode_int_r(self, opcode: int, operands: List[str]) -> int:
        """Encode integer R-type instruction"""
        rd = self.int_regs.get(operands[0], 0)
        ra = self.int_regs.get(operands[1], 0) if len(operands) > 1 else 0
        rb = self.int_regs.get(operands[2], 0) if len(operands) > 2 else 0

        binary = (opcode << 26) | (rd << 21) | (ra << 16) | (rb << 11)
        return binary

    def encode_i(self, opcode: int, operands: List[str]) -> int:
        """Encode I-type instruction"""
        rd = self.parse_register(operands[0])
        rs1 = self.parse_register(operands[1]) if len(operands) > 1 else 0
        imm = self.parse_immediate(operands[2]) if len(operands) > 2 else 0

        # Sign extend and mask to 16 bits
        imm = imm & 0xFFFF

        binary = (opcode << 26) | (rd << 21) | (rs1 << 16) | imm
        return binary

    def encode_memory_i(self, opcode: int, operands: List[str]) -> int:
        """Encode memory I-type: lf fd, offset(ra)"""
        rd = self.parse_register(operands[0])

        # Parse offset(register)
        match = re.match(r'(-?\d+)\((\w+)\)', operands[1])
        if match:
            offset = int(match.group(1))
            rs1 = self.parse_register(match.group(2))
        else:
            offset = 0
            rs1 = 0

        offset = offset & 0xFFFF

        binary = (opcode << 26) | (rd << 21) | (rs1 << 16) | offset
        return binary

    def encode_branch(self, opcode: int, operands: List[str], address: int) -> int:
        """Encode branch instruction"""
        ra = self.parse_register(operands[0])
        rb = self.parse_register(operands[1])

        # Parse label or offset
        target = operands[2]
        if target in self.labels:
            target_addr = self.labels[target]
            offset = (target_addr - address - 4) // 4  # Word offset
        else:
            offset = int(target)

        offset = offset & 0xFFFF

        binary = (opcode << 26) | (ra << 21) | (rb << 16) | offset
        return binary

    def encode_jal(self, opcode: int, operands: List[str], address: int) -> int:
        """Encode JAL instruction"""
        rd = self.parse_register(operands[0])

        # Parse label
        target = operands[1]
        if target in self.labels:
            target_addr = self.labels[target]
        else:
            target_addr = int(target)

        # Encode target address in lower 21 bits
        target_addr = (target_addr >> 2) & 0x1FFFFF

        binary = (opcode << 26) | (rd << 21) | target_addr
        return binary

    def encode_jump(self, opcode: int, operands: List[str], address: int) -> int:
        """Encode JUMP instruction"""
        target = operands[0]
        if target in self.labels:
            target_addr = self.labels[target]
        else:
            target_addr = int(target)

        target_addr = (target_addr >> 2) & 0x3FFFFFF

        binary = (opcode << 26) | target_addr
        return binary

    def encode_load_address(self, operands: List[str]) -> int:
        """Encode LA pseudo-instruction"""
        rd = self.parse_register(operands[0])
        label = operands[1]

        if label in self.labels:
            addr = self.labels[label]
        else:
            addr = 0

        # Encode as LI instruction
        addr = addr & 0x1FFFFF

        binary = (0x36 << 26) | (rd << 21) | addr
        return binary

    def parse_register(self, reg_str: str) -> int:
        """Parse register name"""
        reg_str = reg_str.strip().lower()

        if reg_str in self.int_regs:
            return self.int_regs[reg_str]
        elif reg_str in self.float_regs:
            return self.float_regs[reg_str]
        elif reg_str in self.vector_regs:
            return self.vector_regs[reg_str]

        return 0

    def parse_immediate(self, imm_str: str) -> int:
        """Parse immediate value"""
        imm_str = imm_str.strip()

        if imm_str.startswith('0x'):
            return int(imm_str, 16)
        else:
            return int(imm_str)

    def write_binary(self, output_file: str):
        """Write binary output"""
        with open(output_file, 'wb') as f:
            for instr in self.instructions:
                f.write(struct.pack('<I', instr.binary))


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: assembler.py <input.s> <output.bin>")
        sys.exit(1)

    assembler = RTCoreAssembler()
    assembler.assemble(sys.argv[1], sys.argv[2])
    print("Assembly complete!")
