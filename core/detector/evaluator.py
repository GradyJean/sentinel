import ast
import operator
from typing import Any, Dict, Callable


class SafeExpressionEvaluator(ast.NodeVisitor):
    """
    安全表达式求值器：
    - 支持数学 / 比较 / 布尔
    - 支持字符串等值 / 不等值判断
    - 变量来自 features dict
    """

    ALLOWED_BIN_OPS: Dict[Any, Callable] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
    }

    ALLOWED_CMP_OPS: Dict[Any, Callable] = {
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
    }

    ALLOWED_BOOL_OPS: Dict[Any, Callable] = {
        ast.And: all,
        ast.Or: any,
    }

    ALLOWED_UNARY_OPS: Dict[Any, Callable] = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def __init__(self, variables: Dict[str, Any]):
        self.variables = variables

    def eval(self, expr: str) -> Any:
        tree = ast.parse(expr, mode="eval")
        return self.visit(tree.body)

    def visit_BinOp(self, node: ast.BinOp):
        op = self.ALLOWED_BIN_OPS.get(type(node.op))
        if not op:
            raise ValueError("Unsupported binary operator")
        return op(self.visit(node.left), self.visit(node.right))

    def visit_Compare(self, node: ast.Compare):
        left = self.visit(node.left)
        for op_node, comparator in zip(node.ops, node.comparators):
            op = self.ALLOWED_CMP_OPS.get(type(op_node))
            if not op:
                raise ValueError("Unsupported comparison operator")
            if not op(left, self.visit(comparator)):
                return False
            left = self.visit(comparator)
        return True

    def visit_BoolOp(self, node: ast.BoolOp):
        op = self.ALLOWED_BOOL_OPS.get(type(node.op))
        if not op:
            raise ValueError("Unsupported boolean operator")
        return op(self.visit(v) for v in node.values)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        op = self.ALLOWED_UNARY_OPS.get(type(node.op))
        if not op:
            raise ValueError("Unsupported unary operator")
        return op(self.visit(node.operand))

    def visit_Name(self, node: ast.Name):
        if node.id not in self.variables:
            return 0.0

        value = self.variables[node.id]

        if isinstance(value, (int, float, str, bool)):
            return value

        raise ValueError(
            f"Unsupported variable type for '{node.id}': {type(value)}"
        )

    def visit_Constant(self, node: ast.Constant):
        return node.value

    def generic_visit(self, node):
        raise ValueError(
            f"Unsupported expression element: {type(node).__name__}"
        )