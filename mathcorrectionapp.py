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
st.title("🧮 Streamlit Math Solver — Full Version")

st.markdown("""
Supports:
- `sinx`, `cos x`, `tan(x)` etc.
- `d/dx sinx`, `diff(expr)`
- Solve equations (with multiplicity for polynomials)
- Simplify, Factor, Expand, Integrate, Evaluate numerically
""")

# Sidebar
operation = st.sidebar.selectbox("Choose operation", [
    "Auto (detect operation)", "Solve equation", "Simplify expression",
    "Differentiate", "Integrate (indefinite)", "Factor", "Expand", "Evaluate (numeric)"
])
var_input = st.sidebar.text_input("Variable(s) (comma-separated)", value="x")

MATH_FUNCS = ['sin','cos','tan','sec','csc','cot','asin','acos','atan',
              'sinh','cosh','tanh','exp','log','sqrt']

BASE_LOCAL = {
    'sin':sin,'cos':cos,'tan':tan,'sec':sec,'csc':csc,'cot':cot,
    'asin':__import__('sympy').asin,'acos':__import__('sympy').acos,'atan':__import__('sympy').atan,
    'sinh':__import__('sympy').sinh,'cosh':__import__('sympy').cosh,'tanh':__import__('sympy').tanh,
    'exp':exp,'log':log,'sqrt':sqrt,'pi':pi,'E':E
}

# ----------------- Helper functions -----------------
def normalize_func(s):
    for f in MATH_FUNCS:
        # sinx -> sin(x), sin x -> sin(x)
        s = re.sub(rf'\b{f}\s*([A-Za-z0-9\*\+\-/\^\(\)]+)', f'{f}(\\1)', s)
        s = re.sub(rf'\b{f}([A-Za-z0-9\*\+\-/\^\(\)]+)', f'{f}(\\1)', s)
    return s

def preprocess(s):
    s = s.replace('^','**')
    s = normalize_func(s)
    s = re.sub(r'(\d)([A-Za-z])', r'\1*\2', s)
    s = s.replace(')(', ')*(')
    return s.strip()

def build_local(s):
    local = dict(BASE_LOCAL)
    letters = set(re.findall(r'[a-zA-Z]', s))
    for l in letters:
        if l not in local: local[l] = Symbol(l)
    return local

def parse_input(expr_str):
    s = expr_str.strip()
    # d/dx syntax
    m = re.match(r'd/d([A-Za-z])\s*(.*)', s)
    if m:
        return diff(parse_expr(preprocess(m.group(2)), local_dict=build_local(m.group(2))), symbols(m.group(1)))
    # diff(expr) syntax
    m2 = re.match(r'diff\s*\(\s*(.*)\s*\)', s)
    if m2:
        expr = parse_expr(preprocess(m2.group(1)), local_dict=build_local(m2.group(1)))
        var = list(expr.free_symbols)[0] if expr.free_symbols else symbols("x")
        return diff(expr, var)
    # equation
    if '=' in s:
        left,right = s.split('=',1)
        return Eq(parse_expr(preprocess(left), local_dict=build_local(left)),
                  parse_expr(preprocess(right), local_dict=build_local(right)))
    # expression
    return parse_expr(preprocess(s), local_dict=build_local(s))

# ----------------- UI -----------------
expr_input = st.text_area("Enter expression or equation", height=140, value="d/dx sinx")
if st.button("Run"):
    if not expr_input.strip():
        st.warning("Enter an expression first.")
    else:
        try:
            syms = [Symbol(v.strip()) for v in var_input.split(",") if v.strip()]
            if not syms: syms = [symbols("x")]
            parsed = parse_input(expr_input)

            # Auto-detect
            op = operation
            if operation=="Auto (detect operation)":
                s_low = expr_input.lower()
                if s_low.startswith("d/d") or 'diff(' in s_low: op="Differentiate"
                elif '=' in s_low: op="Solve equation"
                elif 'integrate' in s_low or '∫' in s_low: op="Integrate (indefinite)"
                else: op="Simplify expression"

            expr_val = parsed.lhs - parsed.rhs if isinstance(parsed, Eq) else parsed

            if op=="Solve equation":
                sol = solveset(expr_val, syms[0], domain=S.Complexes)
                st.subheader("Solution set")
                st.write(sol)
                st.latex(latex(sol))
                # Polynomial multiplicities
                try:
                    poly = Poly(expr_val, syms[0])
                    if poly.is_polynomial():
                        rd = roots(expr_val, syms[0])
                        if rd:
                            st.subheader("Polynomial roots (with multiplicity)")
                            st.write([(r,int(m)) for r,m in rd.items()])
                except:
                    pass

            elif op=="Simplify expression":
                res = simplify(expr_val); st.subheader("Simplified"); st.write(res); st.latex(latex(res))
            elif op=="Differentiate":
                res = diff(expr_val, syms[0]); st.subheader("Derivative"); st.write(res); st.latex(latex(res))
            elif op=="Integrate (indefinite)":
                res = integrate(expr_val, syms[0]); st.subheader("Indefinite integral"); st.write(res); st.latex(latex(res))
            elif op=="Factor":
                res = factor(expr_val); st.subheader("Factored"); st.write(res); st.latex(latex(res))
            elif op=="Expand":
                res = expand(expr_val); st.subheader("Expanded"); st.write(res); st.latex(latex(res))
            elif op=="Evaluate (numeric)":
                vals = st.text_input("Assignments e.g. x=2,y=3","")
                if vals.strip():
                    subs = {Symbol(k.strip()):sympify(v.strip()) for pair in vals.split(",") if "=" in pair for k,v in [pair.split("=")]}
                    res = expr_val.evalf(subs=subs); st.subheader("Numeric result"); st.write(res)
                else: st.info("Provide variable assignments.")

        except Exception as e:
            st.error("Error while processing input.")
            st.text(traceback.format_exc())

st.sidebar.markdown("---")
st.sidebar.info("Examples:\n- d/dx sinx -> cos(x)\n- diff(x^3) -> 3*x**2\n- Solve equation: x^2=4\n- Factor: x^2-4")
