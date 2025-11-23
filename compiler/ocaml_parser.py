#!/usr/bin/env python3
"""
OCaml Parser for min-rt.ml
Parses OCaml code into an intermediate representation
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Any
from enum import Enum


class ExprType(Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    ARRAY = "array"
    TUPLE = "tuple"
    FUNCTION = "function"
    UNIT = "unit"


@dataclass
class Expr:
    """Base expression class"""
    type: str

@dataclass
class Const(Expr):
    """Constant value"""
    value: Union[int, float, bool]
    const_type: ExprType

    def __init__(self, value, const_type):
        super().__init__("const")
        self.value = value
        self.const_type = const_type

@dataclass
class Var(Expr):
    """Variable reference"""
    name: str

    def __init__(self, name):
        super().__init__("var")
        self.name = name

@dataclass
class BinOp(Expr):
    """Binary operation"""
    op: str
    left: Expr
    right: Expr

    def __init__(self, op, left, right):
        super().__init__("binop")
        self.op = op
        self.left = left
        self.right = right

@dataclass
class UnOp(Expr):
    """Unary operation"""
    op: str
    operand: Expr

    def __init__(self, op, operand):
        super().__init__("unop")
        self.op = op
        self.operand = operand

@dataclass
class If(Expr):
    """If expression"""
    cond: Expr
    then_expr: Expr
    else_expr: Expr

    def __init__(self, cond, then_expr, else_expr):
        super().__init__("if")
        self.cond = cond
        self.then_expr = then_expr
        self.else_expr = else_expr

@dataclass
class Let(Expr):
    """Let binding"""
    name: str
    value: Expr
    body: Expr
    is_rec: bool = False

    def __init__(self, name, value, body, is_rec=False):
        super().__init__("let")
        self.name = name
        self.value = value
        self.body = body
        self.is_rec = is_rec

@dataclass
class FunDef(Expr):
    """Function definition"""
    name: str
    params: List[str]
    body: Expr
    is_rec: bool = False

    def __init__(self, name, params, body, is_rec=False):
        super().__init__("fundef")
        self.name = name
        self.params = params
        self.body = body
        self.is_rec = is_rec

@dataclass
class FunCall(Expr):
    """Function call"""
    func: str
    args: List[Expr]

    def __init__(self, func, args):
        super().__init__("funcall")
        self.func = func
        self.args = args

@dataclass
class ArrayAccess(Expr):
    """Array access"""
    array: Expr
    index: Expr

    def __init__(self, array, index):
        super().__init__("array_access")
        self.array = array
        self.index = index

@dataclass
class ArrayUpdate(Expr):
    """Array update"""
    array: Expr
    index: Expr
    value: Expr

    def __init__(self, array, index, value):
        super().__init__("array_update")
        self.array = array
        self.index = index
        self.value = value

@dataclass
class Tuple(Expr):
    """Tuple"""
    elements: List[Expr]

    def __init__(self, elements):
        super().__init__("tuple")
        self.elements = elements

@dataclass
class TupleAccess(Expr):
    """Tuple element access"""
    tuple_expr: Expr
    index: int

    def __init__(self, tuple_expr, index):
        super().__init__("tuple_access")
        self.tuple_expr = tuple_expr
        self.index = index

@dataclass
class Seq(Expr):
    """Sequence of expressions"""
    exprs: List[Expr]

    def __init__(self, exprs):
        super().__init__("seq")
        self.exprs = exprs


class OCamlParser:
    """
    Simplified OCaml parser for min-rt.ml
    Handles the subset of OCaml used in the ray tracer
    """

    def __init__(self):
        self.globals = {}
        self.functions = {}

    def parse_file(self, filename: str) -> Dict[str, Any]:
        """Parse an OCaml file"""
        with open(filename, 'r') as f:
            content = f.read()

        # Remove comments
        content = self.remove_comments(content)

        # Parse top-level definitions
        self.parse_top_level(content)

        return {
            'globals': self.globals,
            'functions': self.functions
        }

    def remove_comments(self, content: str) -> str:
        """Remove OCaml comments"""
        # Remove (* ... *) comments
        result = re.sub(r'\(\*.*?\*\)', '', content, flags=re.DOTALL)
        return result

    def parse_top_level(self, content: str):
        """Parse top-level definitions"""
        # Extract let rec function definitions
        # Pattern: let rec function_name params = body

        # For min-rt, we'll focus on extracting function signatures
        # and understanding the structure

        # Extract function names
        func_pattern = r'let\s+rec\s+(\w+)\s+(.*?)\s*='
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            params_str = match.group(2)
            # Store function metadata
            self.functions[func_name] = {
                'name': func_name,
                'params': self.parse_params(params_str),
                'body': None  # Will be filled by detailed parsing
            }

    def parse_params(self, params_str: str) -> List[str]:
        """Parse function parameters"""
        params = params_str.strip().split()
        return [p for p in params if p and not p.startswith('(')]

    def identify_vector_patterns(self, expr: Expr) -> List[tuple]:
        """
        Identify patterns that can be vectorized
        Returns list of (pattern_type, location) tuples
        """
        patterns = []

        # Pattern 1: Three consecutive array accesses arr.(0), arr.(1), arr.(2)
        # Pattern 2: Dot product: a.(0)*b.(0) + a.(1)*b.(1) + a.(2)*b.(2)
        # Pattern 3: Vector normalize

        return patterns


class OCamlToIR:
    """
    Convert OCaml expressions to intermediate representation
    with optimization opportunities marked
    """

    def __init__(self):
        self.vectorizable_vars = set()  # Variables that are 3-element arrays

    def convert(self, expr: Expr, context: Dict) -> Dict:
        """Convert expression to IR"""
        if expr.type == "binop":
            return self.convert_binop(expr, context)
        elif expr.type == "funcall":
            return self.convert_funcall(expr, context)
        # ... other conversions

        return {"type": "unknown", "expr": expr}

    def convert_binop(self, expr: BinOp, context: Dict) -> Dict:
        """Convert binary operation"""
        left = self.convert(expr.left, context)
        right = self.convert(expr.right, context)

        # Check for vectorizable patterns
        if self.is_vector_operation(expr, context):
            return {
                "type": "vector_binop",
                "op": expr.op,
                "left": left,
                "right": right,
                "vectorizable": True
            }

        return {
            "type": "binop",
            "op": expr.op,
            "left": left,
            "right": right
        }

    def convert_funcall(self, expr: FunCall, context: Dict) -> Dict:
        """Convert function call with inlining opportunities"""
        # Check if function should be inlined
        if self.should_inline(expr.func, context):
            return {
                "type": "inline_call",
                "func": expr.func,
                "args": [self.convert(arg, context) for arg in expr.args],
                "inline": True
            }

        return {
            "type": "funcall",
            "func": expr.func,
            "args": [self.convert(arg, context) for arg in expr.args]
        }

    def should_inline(self, func_name: str, context: Dict) -> bool:
        """Determine if function should be inlined"""
        # Inline small accessor functions
        accessor_funcs = [
            'o_texturetype', 'o_form', 'o_reflectiontype',
            'o_param_a', 'o_param_b', 'o_param_c',
            'o_param_x', 'o_param_y', 'o_param_z',
            'o_diffuse', 'o_hilight',
            'o_color_red', 'o_color_green', 'o_color_blue',
            'fsqr', 'fhalf', 'sgn'
        ]
        return func_name in accessor_funcs

    def is_vector_operation(self, expr: Expr, context: Dict) -> bool:
        """Check if expression is a vector operation"""
        # Detect patterns like: v.(0) op w.(0)
        # where v and w are 3-element arrays
        return False  # Placeholder


if __name__ == '__main__':
    parser = OCamlParser()
    result = parser.parse_file('/tmp/min-caml/min-rt/min-rt.ml')

    print(f"Found {len(result['functions'])} functions:")
    for name in list(result['functions'].keys())[:10]:
        print(f"  - {name}")
