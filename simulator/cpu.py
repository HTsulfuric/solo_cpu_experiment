#!/usr/bin/env python3
"""
RTCore-V1 CPU Simulator
Simulates the custom ray tracing CPU architecture.
"""

import sys
import struct
import math
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np


@dataclass
class Vector3:
    """3D vector representation"""
    x: float
    y: float
    z: float

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def length_squared(self) -> float:
        return self.x**2 + self.y**2 + self.z**2

    def normalize(self):
        length = self.length()
        if length > 1e-10:
            return Vector3(self.x / length, self.y / length, self.z / length)
        return Vector3(0, 0, 0)

    def __getitem__(self, idx):
        if idx == 0: return self.x
        if idx == 1: return self.y
        if idx == 2: return self.z
        raise IndexError(f"Vector3 index {idx} out of range")

    def __setitem__(self, idx, value):
        if idx == 0: self.x = value
        elif idx == 1: self.y = value
        elif idx == 2: self.z = value
        else: raise IndexError(f"Vector3 index {idx} out of range")

    def to_array(self):
        return [self.x, self.y, self.z]


class RTCoreV1:
    """RTCore-V1 CPU Simulator"""

    def __init__(self, memory_size=16 * 1024 * 1024):  # 16MB memory
        # Registers
        self.r = [0] * 32  # Integer registers
        self.f = [0.0] * 32  # Float registers
        self.v = [Vector3(0, 0, 0) for _ in range(16)]  # Vector registers

        # Special registers
        self.pc = 0  # Program counter
        self.running = True

        # Memory (byte-addressable)
        self.memory = bytearray(memory_size)

        # Instruction count
        self.instruction_count = 0

        # IO buffers
        self.input_buffer = []
        self.output_buffer = []

        # Instruction decode table
        self.opcodes = {
            # Vector operations
            0x01: self.op_vadd,
            0x02: self.op_vsub,
            0x03: self.op_vmul,
            0x04: self.op_vdot,
            0x05: self.op_vcross,
            0x06: self.op_vnorm,
            0x07: self.op_vlength,
            0x08: self.op_vfma,
            0x09: self.op_vset,
            0x0A: self.op_vget,
            0x0B: self.op_vput,
            0x0C: self.op_vsqr,

            # Scalar FP operations
            0x10: self.op_fadd,
            0x11: self.op_fsub,
            0x12: self.op_fmul,
            0x13: self.op_fdiv,
            0x14: self.op_fsqrt,
            0x15: self.op_fabs,
            0x16: self.op_fneg,
            0x17: self.op_fmin,
            0x18: self.op_fmax,
            0x19: self.op_ffma,
            0x1A: self.op_fmadd,
            0x1B: self.op_fmsub,

            # Integer operations
            0x20: self.op_add,
            0x21: self.op_sub,
            0x22: self.op_mul,
            0x23: self.op_div,
            0x24: self.op_and,
            0x25: self.op_or,
            0x26: self.op_xor,
            0x27: self.op_slt,
            0x28: self.op_addi,

            # Memory operations
            0x30: self.op_lw,
            0x31: self.op_sw,
            0x32: self.op_lf,
            0x33: self.op_sf,
            0x34: self.op_lv,
            0x35: self.op_sv,
            0x36: self.op_li,
            0x37: self.op_lif,

            # Control flow
            0x40: self.op_beq,
            0x41: self.op_bne,
            0x42: self.op_blt,
            0x43: self.op_bge,
            0x44: self.op_fbeq,
            0x45: self.op_fbne,
            0x46: self.op_fblt,
            0x47: self.op_fbge,
            0x48: self.op_jump,
            0x49: self.op_jal,
            0x4A: self.op_jalr,
            0x4B: self.op_ret,

            # System/IO
            0x50: self.op_readf,
            0x51: self.op_readi,
            0x52: self.op_writeb,
            0x53: self.op_writei,
            0x5F: self.op_halt,
        }

    def load_program(self, instructions: List[int], start_addr=0x1000):
        """Load program into memory"""
        self.pc = start_addr
        for i, instr in enumerate(instructions):
            addr = start_addr + i * 4
            self.memory[addr:addr+4] = struct.pack('<I', instr)

    def load_data(self, data: bytes, addr: int):
        """Load data into memory"""
        self.memory[addr:addr+len(data)] = data

    def fetch(self) -> int:
        """Fetch instruction from memory"""
        instr_bytes = self.memory[self.pc:self.pc+4]
        return struct.unpack('<I', instr_bytes)[0]

    def decode_r(self, instr: int) -> Tuple[int, int, int, int]:
        """Decode R-type instruction"""
        opcode = (instr >> 26) & 0x3F
        rd = (instr >> 21) & 0x1F
        rs1 = (instr >> 16) & 0x1F
        rs2 = (instr >> 11) & 0x1F
        return opcode, rd, rs1, rs2

    def decode_i(self, instr: int) -> Tuple[int, int, int, int]:
        """Decode I-type instruction"""
        opcode = (instr >> 26) & 0x3F
        rd = (instr >> 21) & 0x1F
        rs1 = (instr >> 16) & 0x1F
        imm = instr & 0xFFFF
        # Sign extend
        if imm & 0x8000:
            imm |= 0xFFFF0000
        return opcode, rd, rs1, imm

    def execute(self, instr: int):
        """Execute one instruction"""
        opcode = (instr >> 26) & 0x3F

        if opcode in self.opcodes:
            self.opcodes[opcode](instr)
        else:
            raise ValueError(f"Unknown opcode: 0x{opcode:02X} at PC={self.pc:08X}")

        self.instruction_count += 1
        self.r[0] = 0  # R0 always zero
        self.f[0] = 0.0  # F0 always zero
        self.v[0] = Vector3(0, 0, 0)  # V0 always zero

    def run(self, max_instructions=None):
        """Run program until halt or max instructions"""
        while self.running:
            if max_instructions and self.instruction_count >= max_instructions:
                break

            instr = self.fetch()
            self.pc += 4
            self.execute(instr)

    # Vector Operations
    def op_vadd(self, instr):
        _, vd, va, vb = self.decode_r(instr)
        self.v[vd] = self.v[va] + self.v[vb]

    def op_vsub(self, instr):
        _, vd, va, vb = self.decode_r(instr)
        self.v[vd] = self.v[va] - self.v[vb]

    def op_vmul(self, instr):
        _, vd, va, fs = self.decode_r(instr)
        self.v[vd] = self.v[va] * self.f[fs]

    def op_vdot(self, instr):
        _, fd, va, vb = self.decode_r(instr)
        self.f[fd] = self.v[va].dot(self.v[vb])

    def op_vcross(self, instr):
        _, vd, va, vb = self.decode_r(instr)
        self.v[vd] = self.v[va].cross(self.v[vb])

    def op_vnorm(self, instr):
        _, vd, va, _ = self.decode_r(instr)
        self.v[vd] = self.v[va].normalize()

    def op_vlength(self, instr):
        _, fd, va, _ = self.decode_r(instr)
        self.f[fd] = self.v[va].length()

    def op_vfma(self, instr):
        _, vd, va, vb = self.decode_r(instr)
        # Need to extract fs from funct field - simplified
        fs = (instr >> 6) & 0x1F
        self.v[vd] = self.v[va] + self.v[vb] * self.f[fs]

    def op_vset(self, instr):
        _, vd, fx, fy = self.decode_r(instr)
        fz = (instr >> 6) & 0x1F
        self.v[vd] = Vector3(self.f[fx], self.f[fy], self.f[fz])

    def op_vget(self, instr):
        _, fd, va, idx = self.decode_r(instr)
        self.f[fd] = self.v[va][idx]

    def op_vput(self, instr):
        _, vd, va, fs = self.decode_r(instr)
        idx = (instr >> 6) & 0x1F
        self.v[vd] = Vector3(self.v[va].x, self.v[va].y, self.v[va].z)
        self.v[vd][idx] = self.f[fs]

    def op_vsqr(self, instr):
        _, fd, va, _ = self.decode_r(instr)
        self.f[fd] = self.v[va].length_squared()

    # Scalar FP Operations
    def op_fadd(self, instr):
        _, fd, fa, fb = self.decode_r(instr)
        self.f[fd] = self.f[fa] + self.f[fb]

    def op_fsub(self, instr):
        _, fd, fa, fb = self.decode_r(instr)
        self.f[fd] = self.f[fa] - self.f[fb]

    def op_fmul(self, instr):
        _, fd, fa, fb = self.decode_r(instr)
        self.f[fd] = self.f[fa] * self.f[fb]

    def op_fdiv(self, instr):
        _, fd, fa, fb = self.decode_r(instr)
        self.f[fd] = self.f[fa] / self.f[fb] if self.f[fb] != 0 else 0.0

    def op_fsqrt(self, instr):
        _, fd, fa, _ = self.decode_r(instr)
        self.f[fd] = math.sqrt(abs(self.f[fa]))

    def op_fabs(self, instr):
        _, fd, fa, _ = self.decode_r(instr)
        self.f[fd] = abs(self.f[fa])

    def op_fneg(self, instr):
        _, fd, fa, _ = self.decode_r(instr)
        self.f[fd] = -self.f[fa]

    def op_fmin(self, instr):
        _, fd, fa, fb = self.decode_r(instr)
        self.f[fd] = min(self.f[fa], self.f[fb])

    def op_fmax(self, instr):
        _, fd, fa, fb = self.decode_r(instr)
        self.f[fd] = max(self.f[fa], self.f[fb])

    def op_ffma(self, instr):
        _, fd, fa, fb = self.decode_r(instr)
        fc = (instr >> 6) & 0x1F
        self.f[fd] = self.f[fa] * self.f[fb] + self.f[fc]

    def op_fmadd(self, instr):
        _, fd, fa, fb = self.decode_r(instr)
        self.f[fd] = self.f[fd] + self.f[fa] * self.f[fb]

    def op_fmsub(self, instr):
        _, fd, fa, fb = self.decode_r(instr)
        self.f[fd] = self.f[fd] - self.f[fa] * self.f[fb]

    # Integer Operations
    def op_add(self, instr):
        _, rd, ra, rb = self.decode_r(instr)
        self.r[rd] = (self.r[ra] + self.r[rb]) & 0xFFFFFFFFFFFFFFFF

    def op_sub(self, instr):
        _, rd, ra, rb = self.decode_r(instr)
        self.r[rd] = (self.r[ra] - self.r[rb]) & 0xFFFFFFFFFFFFFFFF

    def op_mul(self, instr):
        _, rd, ra, rb = self.decode_r(instr)
        self.r[rd] = (self.r[ra] * self.r[rb]) & 0xFFFFFFFFFFFFFFFF

    def op_div(self, instr):
        _, rd, ra, rb = self.decode_r(instr)
        self.r[rd] = (self.r[ra] // self.r[rb]) if self.r[rb] != 0 else 0

    def op_and(self, instr):
        _, rd, ra, rb = self.decode_r(instr)
        self.r[rd] = self.r[ra] & self.r[rb]

    def op_or(self, instr):
        _, rd, ra, rb = self.decode_r(instr)
        self.r[rd] = self.r[ra] | self.r[rb]

    def op_xor(self, instr):
        _, rd, ra, rb = self.decode_r(instr)
        self.r[rd] = self.r[ra] ^ self.r[rb]

    def op_slt(self, instr):
        _, rd, ra, rb = self.decode_r(instr)
        self.r[rd] = 1 if self.r[ra] < self.r[rb] else 0

    def op_addi(self, instr):
        _, rd, ra, imm = self.decode_i(instr)
        self.r[rd] = (self.r[ra] + imm) & 0xFFFFFFFFFFFFFFFF

    # Memory Operations
    def op_lw(self, instr):
        _, rd, ra, imm = self.decode_i(instr)
        addr = (self.r[ra] + imm) & 0xFFFFFFFF
        self.r[rd] = struct.unpack('<Q', self.memory[addr:addr+8])[0]

    def op_sw(self, instr):
        _, rs, ra, imm = self.decode_i(instr)
        addr = (self.r[ra] + imm) & 0xFFFFFFFF
        self.memory[addr:addr+8] = struct.pack('<Q', self.r[rs])

    def op_lf(self, instr):
        _, fd, ra, imm = self.decode_i(instr)
        addr = (self.r[ra] + imm) & 0xFFFFFFFF
        self.f[fd] = struct.unpack('<d', self.memory[addr:addr+8])[0]

    def op_sf(self, instr):
        _, fs, ra, imm = self.decode_i(instr)
        addr = (self.r[ra] + imm) & 0xFFFFFFFF
        self.memory[addr:addr+8] = struct.pack('<d', self.f[fs])

    def op_lv(self, instr):
        _, vd, ra, imm = self.decode_i(instr)
        addr = (self.r[ra] + imm) & 0xFFFFFFFF
        x, y, z = struct.unpack('<ddd', self.memory[addr:addr+24])
        self.v[vd] = Vector3(x, y, z)

    def op_sv(self, instr):
        _, vs, ra, imm = self.decode_i(instr)
        addr = (self.r[ra] + imm) & 0xFFFFFFFF
        self.memory[addr:addr+24] = struct.pack('<ddd',
            self.v[vs].x, self.v[vs].y, self.v[vs].z)

    def op_li(self, instr):
        opcode = (instr >> 26) & 0x3F
        rd = (instr >> 21) & 0x1F
        imm32 = instr & 0x1FFFFF
        # Sign extend from 21 bits
        if imm32 & 0x100000:
            imm32 |= 0xFFE00000
        self.r[rd] = imm32

    def op_lif(self, instr):
        _, fd, _, imm = self.decode_i(instr)
        # Treat immediate as float literal index or direct value
        self.f[fd] = float(imm)

    # Control Flow
    def op_beq(self, instr):
        opcode, ra, rb, offset = self.decode_i(instr)
        if self.r[ra] == self.r[rb]:
            self.pc = (self.pc + offset - 4) & 0xFFFFFFFF

    def op_bne(self, instr):
        opcode, ra, rb, offset = self.decode_i(instr)
        if self.r[ra] != self.r[rb]:
            self.pc = (self.pc + offset - 4) & 0xFFFFFFFF

    def op_blt(self, instr):
        opcode, ra, rb, offset = self.decode_i(instr)
        if self.r[ra] < self.r[rb]:
            self.pc = (self.pc + offset - 4) & 0xFFFFFFFF

    def op_bge(self, instr):
        opcode, ra, rb, offset = self.decode_i(instr)
        if self.r[ra] >= self.r[rb]:
            self.pc = (self.pc + offset - 4) & 0xFFFFFFFF

    def op_fbeq(self, instr):
        opcode, fa, fb, offset = self.decode_i(instr)
        if abs(self.f[fa] - self.f[fb]) < 1e-10:
            self.pc = (self.pc + offset - 4) & 0xFFFFFFFF

    def op_fbne(self, instr):
        opcode, fa, fb, offset = self.decode_i(instr)
        if abs(self.f[fa] - self.f[fb]) >= 1e-10:
            self.pc = (self.pc + offset - 4) & 0xFFFFFFFF

    def op_fblt(self, instr):
        opcode, fa, fb, offset = self.decode_i(instr)
        if self.f[fa] < self.f[fb]:
            self.pc = (self.pc + offset - 4) & 0xFFFFFFFF

    def op_fbge(self, instr):
        opcode, fa, fb, offset = self.decode_i(instr)
        if self.f[fa] >= self.f[fb]:
            self.pc = (self.pc + offset - 4) & 0xFFFFFFFF

    def op_jump(self, instr):
        target = instr & 0x3FFFFFF
        self.pc = (target << 2) & 0xFFFFFFFF

    def op_jal(self, instr):
        opcode = (instr >> 26) & 0x3F
        rd = (instr >> 21) & 0x1F
        target = (instr & 0x1FFFFF) << 2
        self.r[rd] = self.pc
        self.pc = target

    def op_jalr(self, instr):
        _, rd, ra, _ = self.decode_r(instr)
        self.r[rd] = self.pc
        self.pc = self.r[ra]

    def op_ret(self, instr):
        self.pc = self.r[1]

    # System/IO
    def op_readf(self, instr):
        _, fd, _, _ = self.decode_r(instr)
        if self.input_buffer:
            self.f[fd] = self.input_buffer.pop(0)
        else:
            self.f[fd] = 0.0

    def op_readi(self, instr):
        _, rd, _, _ = self.decode_r(instr)
        if self.input_buffer:
            self.r[rd] = int(self.input_buffer.pop(0))
        else:
            self.r[rd] = 0

    def op_writeb(self, instr):
        _, rs, _, _ = self.decode_r(instr)
        self.output_buffer.append(self.r[rs] & 0xFF)

    def op_writei(self, instr):
        _, rs, _, _ = self.decode_r(instr)
        print(self.r[rs])

    def op_halt(self, instr):
        self.running = False

    def get_stats(self):
        """Return execution statistics"""
        return {
            'instruction_count': self.instruction_count,
            'output_bytes': len(self.output_buffer)
        }


if __name__ == '__main__':
    # Simple test
    cpu = RTCoreV1()
    print("RTCore-V1 CPU Simulator initialized")
    print(f"Memory size: {len(cpu.memory) / 1024 / 1024:.1f} MB")
