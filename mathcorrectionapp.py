# app.py
import streamlit as st
import re
import traceback
from sympy import (
    symbols, Symbol, Eq, S, solveset,
    simplify, factor, expand, diff,
    integrate, latex, sympify, roots, Poly,
    sin, cos, tan, sec, csc, cot, exp, log, sqrt, pi, E
)
from sympy.parsing.sympy_parser import parse_expr

st.set_page_config(page_title="Math Solver", page_icon="🧮", layout="centered")
st.title("🧮 Streamlit Math Solver — Robust Parser")
st.markdown("""
This app:
- handles `sinx`, `sin x`, `sin(x)` (and the same for cos, tan, etc.)
- processes `d/dx sinx`, `d/dx sin(x)`, `diff(...)`
- solves equations, simplifies, factors, expands, integrates and evaluates
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

MATH_FUNCS = ['sin', 'cos', 'tan', 'sec', 'csc', 'cot',
              'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh',
              'exp', 'log', 'sqrt']

BASE_LOCAL = {
    'sin': sin, 'cos': cos, 'tan': tan, 'sec': sec, 'csc': csc, 'cot': cot,
    'asin': __import__('sympy').asin, 'acos': __import__('sympy').acos, 'atan': __import__('sympy').atan,
    'sinh': __import__('sympy').sinh, 'cosh': __import__('sympy').cosh, 'tanh': __import__('sympy').tanh,
    'exp': exp, 'log': log, 'sqrt': sqrt,
    'pi': pi, 'E': E
}

# ---------- Helper functions ----------
def normalize_simple_func(s: str) -> str:
    if not isinstance(s, str): return s
    text = s
    text = re.sub(r'\s+', ' ', text).strip()
    for f in MATH_FUNCS:
        pattern1 = re.compile(rf'\b{f}\s+([A-Za-z0-9\.\*\+\-/\^\_\(\)]+)', flags=re.IGNORECASE)
        text = pattern1.sub(lambda m, f=f: f"{f.lower()}({m.group(1)})", text)
        pattern2 = re.compile(rf'\b{f}([A-Za-z0-9\.\_\^]+)', flags=re.IGNORECASE)
        text = pattern2.sub(lambda m, f=f: f"{f.lower()}({m.group(1)})", text)
        pattern3 = re.compile(rf'\b{f}\s*\(\s*', flags=re.IGNORECASE)
        text = pattern3.sub(f"{f.lower()}(", text)
    return text

def safe_preprocess(s: str) -> str:
    if not isinstance(s, str): return s
    t = s.replace('^', '**')
    t = normalize_simple_func(t)
    t = re.sub(r'(?P<num>\d)(?P<var>[A-Za-z])', r'\g<num>*\g<var>', t)
    t = t.replace(')(', ')*(')
    def name_before_paren(m):
        name = m.group(1)
        if name.lower() in MATH_FUNCS:
            return f"{name.lower()}("
        return f"{name}*("
    t = re.sub(r'([A-Za-z0-9_]+)\(', name_before_paren, t)
    return t.strip()

def find_single_letter_vars(s: str):
    if not isinstance(s, str): return []
    tmp = s
    for f in MATH_FUNCS: tmp = re.sub(rf'\b{re.escape(f)}\b', ' ', tmp, flags=re.IGNORECASE)
    letters = set(re.findall(r'(?<![A-Za-z0-9_])([A-Za-z])(?![A-Za-z0-9_])', tmp))
    return sorted(letters, key=lambda c: (0 if c in ('x','y','t') else 1, c))

def build_local_dict(preprocessed_str: str):
    local = dict(BASE_LOCAL)
    letters = find_single_letter_vars(preprocessed_str)
    for ch in letters:
        if ch.lower() in BASE_LOCAL: continue
        local[ch] = Symbol(ch)
    return local

def parse_expr_with_local(s: str):
    pre = safe_preprocess(s)
    local = build_local_dict(pre)
    return parse_expr(pre, local_dict=local)

def get_symbols_from_input(var_input_str):
    names = [v.strip() for v in var_input_str.split(",") if v.strip()]
    if not names: return (symbols("x"),)
    syms = symbols(" ".join(names))
    return tuple(syms) if isinstance(syms, (tuple, list)) else (syms,)

def parse_input(expr_str):
    s = str(expr_str).strip()
    m = re.match(r'^\s*d/d([A-Za-z])\s*(.*)$', s)
    if m:
        var = symbols(m.group(1))
        rest = m.group(2).strip()
        if rest == '': raise ValueError("No expression to differentiate after d/d<var>")
        return diff(parse_expr_with_local(rest), var)
    m2 = re.match(r'^\s*diff\s*\(\s*(.*)\s*\)\s*$', s)
    if m2:
        inner_expr = parse_expr_with_local(m2.group(1))
        syms = inner_expr.free_symbols
        var = list(syms)[0] if syms else symbols("x")
        return diff(inner_expr, var)
    if '=' in s:
        left, right = s.split('=', 1)
        return Eq(parse_expr_with_local(left), parse_expr_with_local(right))
    return parse_expr_with_local(s)

# ---------- UI ----------
expr_input = st.text_area("Enter expression or equation", height=140,
                          value="d/dx sinx  # try: d/dx sinx, d/dx cosx, d/dx sin(x)")
if st.button("Run"):
    if not expr_input.strip():
        st.warning("Please enter an expression first.")
    else:
        try:
            user_syms = get_symbols_from_input(var_input)
            parsed = parse_input(expr_input)
            op = operation
            if operation == "Auto (detect operation)":
                s_low = expr_input.lower()
                if re.match(r'^\s*d/d', s_low) or 'diff(' in s_low: op = "Differentiate"
                elif '∫' in s_low or 'integrate' in s_low: op = "Integrate (indefinite)"
                elif '=' in s_low: op = "Solve equation"
                else: op = "Simplify expression"

            expr_val = parsed.lhs - parsed.rhs if isinstance(parsed, Eq) else parsed

            if op == "Solve equation":
                target = user_syms[0] if user_syms else symbols("x")
                sol_set = solveset(expr_val, target, domain=S.Complexes)
                st.subheader("Solution set"); st.write(sol_set); st.latex(latex(sol_set))
                try:
                    poly = Poly(expr_val, target)
                    if poly.is_polynomial(): rd = roots(expr_val, target); st.subheader("Polynomial roots (with multiplicity)"); st.write([(r,int(m)) for r,m in rd.items()])
                except: pass

            elif op == "Simplify expression": res = simplify(expr_val); st.subheader("Simplified"); st.write(res); st.latex(latex(res))
            elif op == "Differentiate": res = diff(expr_val, user_syms[0]); st.subheader("Derivative"); st.write(res); st.latex(latex(res))
            elif op == "Integrate (indefinite)": res = integrate(expr_val, user_syms[0]); st.subheader("Indefinite integral"); st.write(res); st.latex(latex(res))
            elif op == "Factor": res = factor(expr_val); st.subheader("Factored"); st.write(res); st.latex(latex(res))
            elif op == "Expand": res = expand(expr_val); st.subheader("Expanded"); st.write(res); st.latex(latex(res))
            elif op == "Evaluate (numeric)":
                vals = st.text_input("Assignments", value=""); 
                if vals.strip():
                    subs = {Symbol(k.strip()): sympify(v.strip()) for pair in vals.split(",") if "=" in pair for k,v in [pair.split("=")]}
                    res = expr_val.evalf(subs=subs); st.subheader("Numeric result"); st.write(res)
                else: st.info("Provide variable assignments to evaluate.")

        except Exception:
            st.error("An error occurred while processing your input.")
            st.text(traceback.format_exc())

st.sidebar.markdown("---")
st.sidebar.info("Examples:\n- d/dx sinx  -> cos(x)\n- d/dx cosx  -> -sin(x)\n- d/dx sin(x) -> cos(x)\n- diff(x^3)   -> 3*x**2")
