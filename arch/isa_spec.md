# RTCore-V1 ISA Specification
## Ray Tracing Optimized Instruction Set Architecture

### Design Philosophy

RTCore-V1 is a custom ISA designed for minimal instruction count on ray tracing workloads.
Key innovations:
1. **Vector-first design**: 3D vectors as first-class citizens
2. **Fused operations**: Complex operations in single instructions
3. **Domain-specific primitives**: Ray-geometry intersection accelerators
4. **Large register file**: Minimize memory traffic

### Register Architecture

#### General Purpose Registers
- **R0-R31**: 64-bit integer registers
  - R0 = constant 0
  - R1 = return address (link register)
  - R2 = stack pointer
  - R3-R31 = general use

#### Floating Point Registers
- **F0-F31**: 64-bit IEEE-754 double precision
  - F0 = constant 0.0
  - F1-F31 = general use

#### Vector Registers
- **V0-V15**: 3×64-bit vectors (3D coordinates)
  - Each vector: {x, y, z} double precision
  - V0 = constant {0, 0, 0}

#### Special Registers
- **PC**: Program counter
- **FLAGS**: Condition flags (zero, negative, carry, overflow)

### Instruction Format

All instructions are 32-bit fixed width.

```
Type R:  [6-bit opcode][5-bit rd][5-bit rs1][5-bit rs2][11-bit funct]
Type I:  [6-bit opcode][5-bit rd][5-bit rs1][16-bit immediate]
Type S:  [6-bit opcode][5-bit rs2][5-bit rs1][16-bit immediate]
Type B:  [6-bit opcode][5-bit rs1][5-bit rs2][16-bit offset]
Type J:  [6-bit opcode][26-bit target]
```

### Instruction Set

#### Vector Operations (Opcode 0x01-0x0F)

| Mnemonic | Format | Opcode | Description |
|----------|--------|--------|-------------|
| VADD | Vd,Va,Vb | 0x01 | Vd = Va + Vb (component-wise) |
| VSUB | Vd,Va,Vb | 0x02 | Vd = Va - Vb |
| VMUL | Vd,Va,Fs | 0x03 | Vd = Va * Fs (scale by scalar) |
| VDOT | Fd,Va,Vb | 0x04 | Fd = Va·Vb (dot product) |
| VCROSS | Vd,Va,Vb | 0x05 | Vd = Va × Vb (cross product) |
| VNORM | Vd,Va | 0x06 | Vd = Va/‖Va‖ (normalize) |
| VLENGTH | Fd,Va | 0x07 | Fd = ‖Va‖ (vector length) |
| VFMA | Vd,Va,Vb,Fs | 0x08 | Vd = Va + Vb*Fs (fused) |
| VSET | Vd,Fx,Fy,Fz | 0x09 | Vd = {Fx,Fy,Fz} |
| VGET | Fd,Va,imm | 0x0A | Fd = Va[imm] (0=x,1=y,2=z) |
| VPUT | Vd,Va,Fs,imm | 0x0B | Vd=Va; Vd[imm]=Fs |
| VSQR | Fd,Va | 0x0C | Fd = ‖Va‖² (length squared) |

#### Scalar Floating Point (Opcode 0x10-0x1F)

| Mnemonic | Format | Opcode | Description |
|----------|--------|--------|-------------|
| FADD | Fd,Fa,Fb | 0x10 | Fd = Fa + Fb |
| FSUB | Fd,Fa,Fb | 0x11 | Fd = Fa - Fb |
| FMUL | Fd,Fa,Fb | 0x12 | Fd = Fa * Fb |
| FDIV | Fd,Fa,Fb | 0x13 | Fd = Fa / Fb |
| FSQRT | Fd,Fa | 0x14 | Fd = √Fa |
| FABS | Fd,Fa | 0x15 | Fd = \|Fa\| |
| FNEG | Fd,Fa | 0x16 | Fd = -Fa |
| FMIN | Fd,Fa,Fb | 0x17 | Fd = min(Fa,Fb) |
| FMAX | Fd,Fa,Fb | 0x18 | Fd = max(Fa,Fb) |
| FFMA | Fd,Fa,Fb,Fc | 0x19 | Fd = Fa*Fb + Fc |
| FMADD | Fd,Fa,Fb | 0x1A | Fd = Fd + Fa*Fb |
| FMSUB | Fd,Fa,Fb | 0x1B | Fd = Fd - Fa*Fb |

#### Integer Operations (Opcode 0x20-0x2F)

| Mnemonic | Format | Opcode | Description |
|----------|--------|--------|-------------|
| ADD | Rd,Ra,Rb | 0x20 | Rd = Ra + Rb |
| SUB | Rd,Ra,Rb | 0x21 | Rd = Ra - Rb |
| MUL | Rd,Ra,Rb | 0x22 | Rd = Ra * Rb |
| DIV | Rd,Ra,Rb | 0x23 | Rd = Ra / Rb |
| AND | Rd,Ra,Rb | 0x24 | Rd = Ra & Rb |
| OR | Rd,Ra,Rb | 0x25 | Rd = Ra \| Rb |
| XOR | Rd,Ra,Rb | 0x26 | Rd = Ra ^ Rb |
| SLT | Rd,Ra,Rb | 0x27 | Rd = (Ra < Rb) ? 1 : 0 |
| ADDI | Rd,Ra,imm | 0x28 | Rd = Ra + imm |

#### Memory Operations (Opcode 0x30-0x3F)

| Mnemonic | Format | Opcode | Description |
|----------|--------|--------|-------------|
| LW | Rd,imm(Ra) | 0x30 | Rd = mem[Ra+imm] (word) |
| SW | Rs,imm(Ra) | 0x31 | mem[Ra+imm] = Rs |
| LF | Fd,imm(Ra) | 0x32 | Fd = mem[Ra+imm] (double) |
| SF | Fs,imm(Ra) | 0x33 | mem[Ra+imm] = Fs |
| LV | Vd,imm(Ra) | 0x34 | Vd = mem[Ra+imm:+24] (3 doubles) |
| SV | Vs,imm(Ra) | 0x35 | mem[Ra+imm:+24] = Vs |
| LI | Rd,imm32 | 0x36 | Rd = imm32 (load immediate) |
| LIF | Fd,imm | 0x37 | Fd = float(imm) (load float literal) |

#### Control Flow (Opcode 0x40-0x4F)

| Mnemonic | Format | Opcode | Description |
|----------|--------|--------|-------------|
| BEQ | Ra,Rb,offset | 0x40 | if (Ra==Rb) PC+=offset |
| BNE | Ra,Rb,offset | 0x41 | if (Ra!=Rb) PC+=offset |
| BLT | Ra,Rb,offset | 0x42 | if (Ra<Rb) PC+=offset |
| BGE | Ra,Rb,offset | 0x43 | if (Ra>=Rb) PC+=offset |
| FBEQ | Fa,Fb,offset | 0x44 | if (Fa==Fb) PC+=offset |
| FBNE | Fa,Fb,offset | 0x45 | if (Fa!=Fb) PC+=offset |
| FBLT | Fa,Fb,offset | 0x46 | if (Fa<Fb) PC+=offset |
| FBGE | Fa,Fb,offset | 0x47 | if (Fa>=Fb) PC+=offset |
| JUMP | target | 0x48 | PC = target |
| JAL | Rd,target | 0x49 | Rd=PC+4; PC=target |
| JALR | Rd,Ra | 0x4A | Rd=PC+4; PC=Ra |
| RET | - | 0x4B | PC = R1 |

#### System/IO (Opcode 0x50-0x5F)

| Mnemonic | Format | Opcode | Description |
|----------|--------|--------|-------------|
| READF | Fd | 0x50 | Fd = read_float() from stdin |
| READI | Rd | 0x51 | Rd = read_int() from stdin |
| WRITEB | Rs | 0x52 | write_byte(Rs) to stdout |
| WRITEI | Rs | 0x53 | write_int(Rs) to stdout |
| HALT | - | 0x5F | Stop execution |

#### Specialized Ray Tracing (Opcode 0x60-0x6F)

These are optional high-level operations for extreme optimization.

| Mnemonic | Format | Opcode | Description |
|----------|--------|--------|-------------|
| RAYSPH | Fd,Vray,Vorg,Vctr,Fr | 0x60 | Ray-sphere intersection distance |
| RAYPLN | Fd,Vray,Vorg,Vnorm,Fd | 0x61 | Ray-plane intersection distance |

### Calling Convention

- **Arguments**: R3-R10 (int), F1-F8 (float), V1-V4 (vector)
- **Return**: R3 (int), F1 (float), V1 (vector)
- **Callee-saved**: R11-R31, F9-F31, V5-V15
- **Caller-saved**: R3-R10, F1-F8, V1-V4
- **Stack**: Grows downward, 8-byte aligned

### Assembly Syntax

```assembly
# Comments start with #
.data              # Data section
  array: .float 1.0, 2.0, 3.0

.text              # Code section
.global main

main:
  # Vector operations
  lv v1, 0(r5)           # Load vector from memory
  lv v2, 24(r5)          # Load second vector
  vdot f1, v1, v2        # Dot product
  vadd v3, v1, v2        # Add vectors

  # Scalar operations
  lif f2, 2.0            # Load immediate float
  vmul v4, v3, f2        # Scale vector

  # Control flow
  fblt f1, f0, skip      # Branch if f1 < 0
  vnorm v4, v4           # Normalize
skip:
  ret                    # Return
```

### Performance Model

- **Vector ops**: 1 cycle (VADD, VSUB, VMUL, VDOT)
- **VNORM**: 4 cycles (sqrt + 3 divides pipelined)
- **Scalar FP**: 1 cycle (add/mul/sub)
- **Scalar DIV/SQRT**: 4 cycles
- **Memory**: 1 cycle (perfect cache)
- **Branches**: 1 cycle (perfect prediction)
- **Control**: 1 cycle

This is an idealized model for instruction counting.
