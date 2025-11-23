# Custom CPU Design for Min-RT Ray Tracing - Implementation Plan

## Project Goal
Design a custom CPU architecture and compiler to execute the min-rt ray tracing program with minimum instruction count for 64x64 rendering of contest.sld.

## Source Analysis

### Min-RT Program Characteristics
- **Source**: OCaml ray tracer (1260 lines)
- **Workload**: Ray tracing with spheres, planes, rectangles, quadric surfaces
- **Features**: Shadows, reflections, texture mapping
- **Data Structures**: Arrays, tuples, global variables
- **Target**: 64x64 pixel rendering (4096 pixels)

### Computational Patterns
1. **Vector Operations** (dominant)
   - Dot products: `v1.(0)*v2.(0) + v1.(1)*v2.(1) + v1.(2)*v2.(2)`
   - Normalization: `sqrt(x^2 + y^2 + z^2)`
   - Vector addition/subtraction
   - Scalar multiplication

2. **Floating Point Math** (heavy)
   - Square root (normalization, distance)
   - Multiply-add patterns (FMA opportunities)
   - Division (ray-object intersection)
   - Trigonometric functions (limited, in initialization)

3. **Control Flow**
   - Deep recursion (raytracing up to 5 levels)
   - Nested conditionals (object type dispatch)
   - Loops (pixel scanning, object iteration)

4. **Memory Access**
   - Array indexing (objects, colors, vectors)
   - Struct field access (object parameters)
   - Global variable reuse

## CPU Architecture Design

### Core Philosophy
**Minimize instructions through:**
1. Vector/SIMD instructions for 3D operations
2. Fused operations (FMA, dot-product-accumulate)
3. Specialized ray tracing primitives
4. Large register file to avoid memory traffic
5. Aggressive function inlining

### Instruction Set Architecture (ISA)

**Name**: RTCore-V1 (Ray Tracing Core, Version 1)

**Register Architecture**:
- 32 general-purpose registers (R0-R31), R0 hardwired to 0
- 32 floating-point registers (F0-F31) - 64-bit double precision
- 16 vector registers (V0-V15) - each holds 3x64-bit floats (3D vectors)
- Special registers: PC, SP, FLAGS

**Instruction Categories**:

1. **Vector Operations** (minimize instruction count)
   - `VDOT Vd, Va, Vb` - 3D dot product in 1 instruction
   - `VNORM Vd, Va` - normalize vector (sqrt + 3 divides)
   - `VADD Vd, Va, Vb` - vector addition
   - `VSUB Vd, Va, Vb` - vector subtraction
   - `VSCALE Vd, Va, Fs` - vector * scalar
   - `VFMA Vd, Va, Vb, Fs` - fused multiply-add: Vd = Va + Vb*Fs
   - `VCROSS Vd, Va, Vb` - cross product

2. **Scalar FP Operations**
   - `FADD Fd, Fa, Fb` - floating add
   - `FSUB Fd, Fa, Fb` - floating subtract
   - `FMUL Fd, Fa, Fb` - floating multiply
   - `FDIV Fd, Fa, Fb` - floating divide
   - `FSQRT Fd, Fa` - square root
   - `FFMA Fd, Fa, Fb, Fc` - fused: Fd = Fa*Fb + Fc
   - `FABS Fd, Fa` - absolute value
   - `FNEG Fd, Fa` - negate

3. **Integer/Logic Operations**
   - `ADD Rd, Ra, Rb` - integer add
   - `SUB Rd, Ra, Rb` - integer subtract
   - `MUL Rd, Ra, Rb` - integer multiply
   - `AND/OR/XOR Rd, Ra, Rb` - bitwise ops
   - `SLT Rd, Ra, Rb` - set less than

4. **Memory Operations**
   - `LW Rd, offset(Ra)` - load word
   - `SW Rs, offset(Ra)` - store word
   - `LF Fd, offset(Ra)` - load float
   - `SF Fs, offset(Ra)` - store float
   - `LV Vd, offset(Ra)` - load vector (3 floats)
   - `SV Vs, offset(Ra)` - store vector (3 floats)

5. **Control Flow**
   - `BEQ/BNE/BLT/BGE Ra, Rb, offset` - branches
   - `FBLT/FBGE Fa, Fb, offset` - FP branches
   - `JUMP addr` - unconditional jump
   - `JAL Rd, addr` - jump and link (call)
   - `JALR Rd, Ra` - indirect jump
   - `RET` - return

6. **Specialized Ray Tracing Operations** (optional, for extreme optimization)
   - `RAYSPHERE Fd, Vray, Vorg, Vsph, Fsphrad` - ray-sphere intersection
   - `RAYPLANE Fd, Vray, Vorg, Vplane, Fplanedist` - ray-plane intersection

**Encoding**: 32-bit fixed-width instructions (RISC-style)

### Compiler Design

**Strategy**: Multi-pass optimizing compiler

**Compilation Pipeline**:
1. **OCaml AST Parsing** - parse min-rt.ml
2. **Lambda Lifting** - convert to flat function representation
3. **Inlining** - aggressive inlining of small functions (object accessors)
4. **SSA Conversion** - Static Single Assignment form
5. **Optimization Passes**:
   - Constant propagation/folding
   - Dead code elimination
   - Common subexpression elimination
   - Loop unrolling (small fixed loops)
   - Vectorization (identify 3-element array ops → vector ops)
   - FMA fusion (a*b+c patterns)
   - Register allocation (graph coloring)
6. **Code Generation** - emit RTCore-V1 assembly
7. **Peephole Optimization** - local pattern matching

**Key Optimizations**:
- Recognize vector patterns: `arr.(0), arr.(1), arr.(2)` → vector register
- Fuse multiply-adds: `a *. b +. c` → FFMA
- Inline all accessor functions (o_param_x, o_param_y, etc.)
- Unroll pixel iteration loops
- Tail call optimization

## Implementation Tasks

### Phase 1: Architecture Definition
- [x] Define complete ISA specification
- [ ] Document instruction encodings
- [ ] Create assembly language syntax

### Phase 2: Compiler Development
- [ ] Implement OCaml parser (simplified, min-rt specific)
- [ ] Build intermediate representation (IR)
- [ ] Implement optimization passes
- [ ] Implement code generator
- [ ] Create assembler (text → binary)

### Phase 3: Simulator Development
- [ ] Implement CPU state (registers, memory)
- [ ] Implement instruction decoder
- [ ] Implement execution engine
- [ ] Add instruction counting
- [ ] Add I/O support (read_float, print_byte)

### Phase 4: Integration & Testing
- [ ] Compile min-rt.ml to assembly
- [ ] Load contest.sld data
- [ ] Run simulation at 64x64
- [ ] Verify output correctness (PPM format)
- [ ] Count total instructions

### Phase 5: Optimization
- [ ] Profile instruction distribution
- [ ] Identify hotspots
- [ ] Tune compiler heuristics
- [ ] Add more specialized instructions if beneficial
- [ ] Iterate until instruction count minimized

## Success Metrics

- **Primary**: Minimum total instruction count for 64x64 contest.sld rendering
- **Secondary**: Correct PPM output (visual verification)
- **Tertiary**: Cycle count (with 1 CPI assumption)

## Deliverables

1. `arch/isa_spec.md` - Complete ISA documentation
2. `compiler/` - Full compiler implementation
3. `simulator/` - CPU simulator
4. `results/` - Simulation results
   - `results/instruction_count.txt` - Total instruction count
   - `results/output.ppm` - Rendered image
   - `results/instruction_trace.txt` - Execution trace
   - `results/profile.txt` - Instruction usage statistics

## Technology Stack

- **Language**: Python (for rapid prototyping)
- **Parser**: Custom recursive descent or use OCaml lexer/parser
- **Data Format**: JSON for IR, text for assembly

## Estimated Complexity

- **Lines of Code**: ~3000-5000
- **Implementation Time**: Complex multi-day project
- **Key Challenges**:
  - Accurate OCaml semantics preservation
  - Effective vectorization detection
  - Correct floating-point handling
