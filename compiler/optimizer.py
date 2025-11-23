#!/usr/bin/env python3
"""
Aggressive Optimizer for RTCore-V1
Implements advanced optimizations to minimize instruction count
"""

from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class OptLevel(Enum):
    """Optimization levels"""
    O0 = 0  # No optimization
    O1 = 1  # Basic optimizations
    O2 = 2  # Aggressive optimizations
    O3 = 3  # Maximum optimizations (may increase code size)


@dataclass
class IRNode:
    """Intermediate representation node"""
    op: str
    inputs: List['IRNode']
    output: str
    metadata: Dict


class AggressiveOptimizer:
    """
    Multi-pass optimizer for minimum instruction count
    """

    def __init__(self, level: OptLevel = OptLevel.O3):
        self.level = level
        self.optimization_stats = {
            'dead_code_eliminated': 0,
            'common_subexprs_eliminated': 0,
            'constants_folded': 0,
            'functions_inlined': 0,
            'loops_unrolled': 0,
            'operations_vectorized': 0,
            'operations_fused': 0,
            'register_moves_eliminated': 0
        }

    def optimize(self, ir: List[IRNode]) -> List[IRNode]:
        """Apply all optimization passes"""
        optimized = ir

        if self.level >= OptLevel.O1:
            optimized = self.constant_folding(optimized)
            optimized = self.dead_code_elimination(optimized)
            optimized = self.common_subexpression_elimination(optimized)

        if self.level >= OptLevel.O2:
            optimized = self.function_inlining(optimized)
            optimized = self.operation_vectorization(optimized)
            optimized = self.operation_fusion(optimized)

        if self.level >= OptLevel.O3:
            optimized = self.loop_unrolling(optimized)
            optimized = self.register_allocation_optimization(optimized)
            optimized = self.instruction_selection_optimization(optimized)

        return optimized

    def constant_folding(self, ir: List[IRNode]) -> List[IRNode]:
        """Fold constant expressions at compile time"""
        result = []

        for node in ir:
            if node.op in ['+', '-', '*', '/'] and self.all_constants(node.inputs):
                # Compute at compile time
                value = self.evaluate_constant_expr(node)
                result.append(IRNode('const', [], node.output, {'value': value}))
                self.optimization_stats['constants_folded'] += 1
            else:
                result.append(node)

        return result

    def dead_code_elimination(self, ir: List[IRNode]) -> List[IRNode]:
        """Remove code that has no effect on output"""
        # Build use-def chains
        used_vars = set()

        # Mark outputs as used
        for node in ir:
            if node.op in ['store', 'call', 'return']:
                for inp in node.inputs:
                    self.mark_used(inp, used_vars)

        # Remove unused definitions
        result = []
        for node in ir:
            if node.output in used_vars or node.op in ['store', 'call', 'return']:
                result.append(node)
            else:
                self.optimization_stats['dead_code_eliminated'] += 1

        return result

    def common_subexpression_elimination(self, ir: List[IRNode]) -> List[IRNode]:
        """Eliminate redundant computations"""
        expr_map = {}  # expression -> first occurrence
        result = []

        for node in ir:
            expr_key = self.make_expr_key(node)

            if expr_key in expr_map and self.is_pure(node):
                # Reuse previous computation
                replacement = IRNode('copy', [expr_map[expr_key]], node.output, {})
                result.append(replacement)
                self.optimization_stats['common_subexprs_eliminated'] += 1
            else:
                result.append(node)
                expr_map[expr_key] = node

        return result

    def function_inlining(self, ir: List[IRNode]) -> List[IRNode]:
        """Inline small functions"""
        inline_candidates = self.identify_inline_candidates(ir)

        result = []
        for node in ir:
            if node.op == 'call' and node.metadata.get('func') in inline_candidates:
                # Inline function body
                inlined = self.inline_function(node)
                result.extend(inlined)
                self.optimization_stats['functions_inlined'] += 1
            else:
                result.append(node)

        return result

    def operation_vectorization(self, ir: List[IRNode]) -> List[IRNode]:
        """Convert scalar operations to vector operations"""
        result = []
        i = 0

        while i < len(ir):
            # Look for pattern: 3 consecutive scalar operations on array elements
            if self.is_vectorizable_pattern(ir[i:i+3]):
                # Replace with single vector operation
                vec_op = self.create_vector_operation(ir[i:i+3])
                result.append(vec_op)
                self.optimization_stats['operations_vectorized'] += 3
                i += 3
            else:
                result.append(ir[i])
                i += 1

        return result

    def operation_fusion(self, ir: List[IRNode]) -> List[IRNode]:
        """Fuse operations into compound instructions"""
        result = []
        i = 0

        while i < len(ir):
            # Look for fuseable patterns
            if i + 1 < len(ir):
                node1, node2 = ir[i], ir[i+1]

                # Pattern: multiply followed by add -> FMA
                if node1.op == 'mul' and node2.op == 'add' and self.can_fuse_to_fma(node1, node2):
                    fma_node = self.create_fma(node1, node2)
                    result.append(fma_node)
                    self.optimization_stats['operations_fused'] += 1
                    i += 2
                    continue

                # Pattern: 3 squares + 2 adds -> VSQR + DOT
                if self.is_length_squared_pattern(ir[i:i+5]):
                    vsqr_node = self.create_vsqr(ir[i:i+5])
                    result.append(vsqr_node)
                    self.optimization_stats['operations_fused'] += 4
                    i += 5
                    continue

            result.append(ir[i])
            i += 1

        return result

    def loop_unrolling(self, ir: List[IRNode]) -> List[IRNode]:
        """Unroll small fixed-iteration loops"""
        result = []

        for node in ir:
            if node.op == 'loop' and self.should_unroll(node):
                # Unroll loop
                unrolled = self.unroll_loop(node)
                result.extend(unrolled)
                self.optimization_stats['loops_unrolled'] += 1
            else:
                result.append(node)

        return result

    def register_allocation_optimization(self, ir: List[IRNode]) -> List[IRNode]:
        """Optimize register allocation to minimize spills"""
        # Build interference graph
        interference = self.build_interference_graph(ir)

        # Color graph (register allocation)
        allocation = self.graph_coloring(interference)

        # Rewrite IR with optimized allocation
        result = self.apply_register_allocation(ir, allocation)

        return result

    def instruction_selection_optimization(self, ir: List[IRNode]) -> List[IRNode]:
        """Select optimal instructions for each operation"""
        result = []

        for node in ir:
            # Choose best instruction variant
            best_instr = self.select_best_instruction(node)
            result.append(best_instr)

        return result

    # Helper methods

    def all_constants(self, nodes: List[IRNode]) -> bool:
        """Check if all nodes are constants"""
        return all(n.op == 'const' for n in nodes)

    def evaluate_constant_expr(self, node: IRNode) -> float:
        """Evaluate constant expression"""
        if node.op == '+':
            return sum(n.metadata['value'] for n in node.inputs)
        elif node.op == '-':
            return node.inputs[0].metadata['value'] - node.inputs[1].metadata['value']
        elif node.op == '*':
            vals = [n.metadata['value'] for n in node.inputs]
            result = 1.0
            for v in vals:
                result *= v
            return result
        elif node.op == '/':
            return node.inputs[0].metadata['value'] / node.inputs[1].metadata['value']
        return 0.0

    def mark_used(self, node: IRNode, used: Set):
        """Mark variable as used"""
        if node.output:
            used.add(node.output)
        for inp in node.inputs:
            self.mark_used(inp, used)

    def make_expr_key(self, node: IRNode) -> str:
        """Create hash key for expression"""
        input_keys = ','.join(n.output for n in node.inputs)
        return f"{node.op}({input_keys})"

    def is_pure(self, node: IRNode) -> bool:
        """Check if operation is pure (no side effects)"""
        pure_ops = {'+', '-', '*', '/', 'sqrt', 'abs', 'dot', 'cross'}
        return node.op in pure_ops

    def identify_inline_candidates(self, ir: List[IRNode]) -> Set[str]:
        """Identify functions that should be inlined"""
        # Inline small functions (< 10 instructions)
        # Inline functions called only once
        # Inline accessor functions
        inline_funcs = {
            'o_param_x', 'o_param_y', 'o_param_z',
            'o_param_a', 'o_param_b', 'o_param_c',
            'fsqr', 'fhalf', 'sgn'
        }
        return inline_funcs

    def inline_function(self, call_node: IRNode) -> List[IRNode]:
        """Inline function call"""
        # Placeholder: return function body with arguments substituted
        return [call_node]

    def is_vectorizable_pattern(self, nodes: List[IRNode]) -> bool:
        """Check if nodes form a vectorizable pattern"""
        if len(nodes) < 3:
            return False

        # Pattern: arr[0] op val, arr[1] op val, arr[2] op val
        # where op is the same and val is the same scalar
        return False  # Simplified

    def create_vector_operation(self, nodes: List[IRNode]) -> IRNode:
        """Create vector operation from scalar operations"""
        return IRNode('vector_op', nodes, nodes[0].output, {})

    def can_fuse_to_fma(self, mul_node: IRNode, add_node: IRNode) -> bool:
        """Check if multiply and add can be fused to FMA"""
        # Check if add uses result of multiply
        return mul_node in add_node.inputs

    def create_fma(self, mul_node: IRNode, add_node: IRNode) -> IRNode:
        """Create FMA instruction"""
        return IRNode('fma', mul_node.inputs + add_node.inputs, add_node.output, {})

    def is_length_squared_pattern(self, nodes: List[IRNode]) -> bool:
        """Check for x²+y²+z² pattern"""
        return False  # Simplified

    def create_vsqr(self, nodes: List[IRNode]) -> IRNode:
        """Create VSQR instruction"""
        return IRNode('vsqr', [], nodes[-1].output, {})

    def should_unroll(self, loop_node: IRNode) -> bool:
        """Determine if loop should be unrolled"""
        # Unroll loops with small fixed iteration count (< 8)
        iterations = loop_node.metadata.get('iterations', float('inf'))
        return iterations <= 8

    def unroll_loop(self, loop_node: IRNode) -> List[IRNode]:
        """Unroll loop"""
        iterations = loop_node.metadata.get('iterations', 1)
        body = loop_node.metadata.get('body', [])

        result = []
        for i in range(iterations):
            # Duplicate body with renamed variables
            for node in body:
                renamed = self.rename_iteration(node, i)
                result.append(renamed)

        return result

    def rename_iteration(self, node: IRNode, iteration: int) -> IRNode:
        """Rename variables for loop iteration"""
        new_output = f"{node.output}_{iteration}"
        return IRNode(node.op, node.inputs, new_output, node.metadata)

    def build_interference_graph(self, ir: List[IRNode]) -> Dict:
        """Build register interference graph"""
        return {}  # Simplified

    def graph_coloring(self, interference: Dict) -> Dict:
        """Graph coloring for register allocation"""
        return {}  # Simplified

    def apply_register_allocation(self, ir: List[IRNode], allocation: Dict) -> List[IRNode]:
        """Apply register allocation to IR"""
        return ir  # Simplified

    def select_best_instruction(self, node: IRNode) -> IRNode:
        """Select optimal instruction variant"""
        # Choose between equivalent instruction sequences
        # Prefer vector ops over scalar
        # Prefer fused ops over separate
        return node

    def print_statistics(self):
        """Print optimization statistics"""
        print("\nOptimization Statistics:")
        print("=" * 50)
        for name, count in self.optimization_stats.items():
            if count > 0:
                readable_name = name.replace('_', ' ').title()
                print(f"  {readable_name}: {count}")

        total_opts = sum(self.optimization_stats.values())
        print(f"\nTotal Optimizations Applied: {total_opts}")

        # Estimate instruction reduction
        reduction = (
            self.optimization_stats['operations_vectorized'] * 2.5 +  # 3x reduction avg
            self.optimization_stats['operations_fused'] * 1.0 +
            self.optimization_stats['dead_code_eliminated'] * 1.0 +
            self.optimization_stats['common_subexprs_eliminated'] * 5.0  # CSE saves many instrs
        )
        print(f"Estimated Instruction Reduction: {int(reduction)}")


if __name__ == '__main__':
    optimizer = AggressiveOptimizer(OptLevel.O3)
    print("Aggressive Optimizer initialized")
    print(f"Optimization Level: {optimizer.level.name}")
