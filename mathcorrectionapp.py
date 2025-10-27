# app.py - Streamlit Math Solver (fixed parser with local_dict)
import streamlit as st
from sympy import (
    symbols, Symbol, Eq, S, solveset,
    simplify, factor, expand, diff,
    integrate, latex, sympify, roots, Poly,
    sin, cos, tan, sec, csc, cot, exp, log, sqrt
)
from sympy.parsing.sympy_parser import parse_expr
from sympy.core.sympify import SympifyError
import re
import traceback

st.set_page_config(page_title="Math Solver", page_icon="🧮", layout="centered")
st.title("🧮 Streamlit Math Solver")
st.markdown("""
Features:
- Solve equations: `x^2 + 6x + 9 = 0`
- Differentiate: `d/dx sinx`, `d/dx sin(x)`, `diff(x^3)`
- Integrate / Simplify / Factor / Expand / Evaluate
Supports `sinx` and `sin(x)` (and other common functions).
""")

operation = st.sidebar.selectbox(
    "Choose operation",
    [
        "Auto (detect operation)",
        "Solve equation",
        "Simplify expression",
        "Differentiate",
        "Integrate (indefinite)",
        "Factor",
        "Expand",
        "Evaluate (numeric)",
    ],
)

var_input = st.sidebar.text_input("Variable(s) (comma-separated)", value="x")

# Known math function names we should treat specially
MATH_FUNCS = ['sin', 'cos', 'tan', 'sec', 'csc', 'cot', 'exp', 'log', 'sqrt', 'asin', 'acos', 'atan']

# Local dictionary for parse_expr so 'sin' is parsed as sympy.sin, not a symbol
LOCAL_DICT = {
    'sin': sin, 'cos': cos, 'tan': tan, 'sec': sec, 'csc': csc, 'cot': cot,
    'exp': exp, 'log': log, 'sqrt': sqrt,
    # common constants
    'pi': __import__('sympy').pi, 'E': __import__('sympy').E
}

# ---------- Helper functions ----------
def preprocess_input(expr_str: str) -> str:
    """Make user-friendly math into something SymPy can parse.

    - ^ -> **
    - 2x -> 2*x
    - x(x+1) -> x*(x+1)
    - keep sin(x) as-is; convert sinx or sin x -> sin(x)
    """
    if not isinstance(expr_str, str):
        return expr_str
    s = expr_str.strip()

    # ^ to **
    s = s.replace('^', '**')

    # normalize whitespace
    s = re.sub(r'\s+', ' ', s)

    # Prepare function regex group
    funcs = '|'.join(map(re.escape, MATH_FUNCS))

    # 1) Convert "func ( ... " with possible space to func(
    s = re.sub(rf'\b({funcs})\s*\(\s*', lambda m: f"{m.group(1)}(", s)

    # 2) Convert "func token" -> "func(token)" where token is a simple expression token
    s = re.sub(
        rf'\b({funcs})\s+([A-Za-z0-9\.\*\+\-/\^\_\(\)]+)',
        lambda m: f"{m.group(1)}({m.group(2)})",
        s
    )

    # 3) Convert "funcX" (no space), like sinx or sin2x -> sin(x) or sin(2x)
    s = re.sub(
        rf'\b({funcs})([A-Za-z0-9\.\_\^]+)',
        lambda m: f"{m.group(1)}({m.group(2)})",
        s
    )

    # 4) Insert * between number and variable: 2x -> 2*x (but after function processing)
    s = re.sub(r'(?P<num>\d)(?P<var>[A-Za-z])', r'\g<num>*\g<var>', s)

    # 5) Insert * between name and '(' if it's not a known function
    def add_mul_between_before_paren(match):
        name = match.group(1)
        if name in MATH_FUNCS:
            return f"{name}("
        return f"{name}*("

    s = re.sub(r'([A-Za-z0-9_]+)\(', add_mul_between_before_paren, s)

    # 6) ensure ')(' -> ')*('
    s = s.replace(')(', ')*(')

    return s.strip()

def get_symbols_from_input(var_input_str):
    names = [v.strip() for v in var_input_str.split(",") if v.strip()]
    if not names:
        return (symbols("x"),)
    syms = symbols(" ".join(names))
    if isinstance(syms, (tuple, list)):
        return tuple(syms)
    return (syms,)

def parse_expr_with_local(s: str):
    """Wrapper around parse_expr to always pass the LOCAL_DICT."""
    return parse_expr(s, local_dict=LOCAL_DICT)

def parse_input(expr_str):
    """Parse user's input into either a SymPy Eq or an expression or a differentiated expression."""
    s = preprocess_input(expr_str)

    # Handle d/dx ...  (e.g., d/dx sin(x) or d/dx (x^2))
    ddx_match = re.match(r'^\s*d/d([A-Za-z])\s*(.*)$', s)
    if ddx_match:
        var = symbols(ddx_match.group(1))
        rest = ddx_match.group(2).strip()
        if rest == '':
            raise ValueError("No expression after d/d{var}")
        return diff(parse_expr_with_local(rest), var)

    # Handle diff(expr) form
    diff_match = re.match(r'^\s*diff\s*\(\s*(.*)\s*\)\s*$', s)
    if diff_match:
        inner = diff_match.group(1)
        inner_expr = parse_expr_with_local(inner)
        syms = inner_expr.free_symbols
        var = list(syms)[0] if syms else symbols("x")
        return diff(inner_expr, var)

    # If contains '=' treat as equation
    if '=' in s:
        left, right = s.split('=', 1)
        left_e = parse_expr_with_local(left)
        right_e = parse_expr_with_local(right)
        return Eq(left_e, right_e)

    # otherwise plain expression
    return parse_expr_with_local(s)


# ---------- UI ----------
expr_input = st.text_area("Enter expression or equation", height=140, value="d/dx sinx  # try: d/dx sinx or d/dx sin(x)")
if st.button("Run"):
    if not expr_input.strip():
        st.warning("Please enter an expression first.")
    else:
        try:
            user_syms = get_symbols_from_input(var_input)
            parsed = parse_input(expr_input)

            # Auto-detect operation if requested
            auto_detect = operation == "Auto (detect operation)"
            op = operation
            if auto_detect:
                s_low = expr_input.lower()
                if re.match(r'^\s*d/d', s_low) or 'diff(' in s_low:
                    op = "Differentiate"
                elif '∫' in s_low or 'integrate' in s_low:
                    op = "Integrate (indefinite)"
                elif '=' in s_low:
                    op = "Solve equation"
                else:
                    op = "Simplify expression"

            # --- Solve Equation ---
            if op == "Solve equation":
                expr_for_solving = parsed.lhs - parsed.rhs if isinstance(parsed, Eq) else parsed
                target = user_syms[0] if len(user_syms) > 0 else symbols("x")
                if isinstance(target, (list, tuple)):
                    target = target[0]
                sol_set = solveset(expr_for_solving, target, domain=S.Complexes)
                st.subheader("Solution set (solveset)")
                st.write(sol_set)
                try:
                    st.latex(latex(sol_set))
                except Exception:
                    pass

                # If polynomial, show multiplicities
                try:
                    poly = Poly(expr_for_solving, target)
                    if poly.is_polynomial():
                        root_dict = roots(expr_for_solving, target)
                        if root_dict:
                            st.subheader("Polynomial roots (with multiplicity)")
                            st.write([(r, int(m)) for r, m in root_dict.items()])
                except Exception:
                    pass

            # --- Simplify ---
            elif op == "Simplify expression":
                expr_val = parsed.lhs - parsed.rhs if isinstance(parsed, Eq) else parsed
                res = simplify(expr_val)
                st.subheader("Simplified")
                st.write(res)
                st.latex(latex(res))

            # --- Differentiate ---
            elif op == "Differentiate":
                # parsed may already be a derivative if parse_input handled d/dx or diff
                if isinstance(parsed, Eq):
                    expr_val = parsed.lhs - parsed.rhs
                else:
                    expr_val = parsed
                # If parse_input returned a deriv, it will be an expression (diff object). Use as-is.
                # Otherwise, differentiate wrt first user symbol.
                # We don't rely on expr_val.has(diff) because expr_val might be a plain expression.
                if expr_val.func.__name__ == 'Derivative':
                    res = expr_val
                else:
                    target = user_syms[0] if len(user_syms) > 0 else symbols("x")
                    if isinstance(target, (list, tuple)):
                        target = target[0]
                    res = diff(expr_val, target)
                st.subheader("Derivative")
                st.write(res)
                st.latex(latex(res))

            # --- Integrate ---
            elif op == "Integrate (indefinite)":
                expr_val = parsed.lhs - parsed.rhs if isinstance(parsed, Eq) else parsed
                target = user_syms[0] if len(user_syms) > 0 else symbols("x")
                if isinstance(target, (list, tuple)):
                    target = target[0]
                res = integrate(expr_val, target)
                st.subheader("Indefinite integral")
                st.write(res)
                st.latex(latex(res))

            # --- Factor ---
            elif op == "Factor":
                expr_val = parsed.lhs - parsed.rhs if isinstance(parsed, Eq) else parsed
                res = factor(expr_val)
                st.subheader("Factored")
                st.write(res)
                st.latex(latex(res))

            # --- Expand ---
            elif op == "Expand":
                expr_val = parsed.lhs - parsed.rhs if isinstance(parsed, Eq) else parsed
                res = expand(expr_val)
                st.subheader("Expanded")
                st.write(res)
                st.latex(latex(res))

            # --- Evaluate numeric ---
            elif op == "Evaluate (numeric)":
                st.write("Enter values, e.g. `x=2, y=3`")
                vals = st.text_input("Assignments", value="")
                expr_val = parsed.lhs - parsed.rhs if isinstance(parsed, Eq) else parsed
                if vals.strip():
                    subs = {}
                    for pair in vals.split(","):
                        if "=" in pair:
                            k, v = pair.split("=")
                            subs[Symbol(k.strip())] = sympify(v.strip())
                    res = expr_val.evalf(subs=subs)
                    st.subheader("Numeric result")
                    st.write(res)
                else:
                    st.info("Provide variable assignments to evaluate.")

        except SympifyError:
            st.error("Could not parse expression. Try adding parentheses or use '**' for power.")
        except Exception as e:
            st.error("An error occurred while processing the input.")
            st.text(traceback.format_exc())

st.sidebar.markdown("---")
st.sidebar.info("Examples:\n- x^2 + 6x + 9 = 0\n- d/dx sinx   (works)\n- d/dx sin(x)\n- diff(x^3)\n- ∫ x^2")
