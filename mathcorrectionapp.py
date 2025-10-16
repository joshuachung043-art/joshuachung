# app.py
import streamlit as st
from sympy import Eq, solve, simplify, factor, expand, SympifyError
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from sympy.printing.latex import latex

# -----------------------------
# Helper setup
# -----------------------------
TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

COMMON_REPLACEMENTS = {
    "×": "*",
    "✕": "*",
    "·": "*",
    "÷": "/",
    "∕": "/",
    "^": "**",
    "—": "-",
    "–": "-",
    "−": "-",
}

def clean_input(s: str) -> str:
    """Fix common math typos."""
    if not s:
        return ""
    s = s.strip()
    for k, v in COMMON_REPLACEMENTS.items():
        s = s.replace(k, v)
    s = s.replace(",", "")
    s = s.replace(" = ", "=").replace(" =", "=").replace("= ", "=")
    return s

def try_parse_expression(expr_text: str):
    """Return parsed SymPy expression."""
    return parse_expr(expr_text, transformations=TRANSFORMS)

def solve_input(text: str):
    corrected = clean_input(text)
    result = {
        "original": text,
        "corrected": corrected,
        "parsed": None,
        "simplified": None,
        "factor": None,
        "expand": None,
        "solution": None,
        "error": None,
    }

    try:
        if "=" in corrected:
            left_s, right_s = corrected.split("=", 1)
            left = try_parse_expression(left_s)
            right = try_parse_expression(right_s)
            result["parsed"] = Eq(left, right)

            eq_expr = simplify(left - right)
            result["simplified"] = Eq(eq_expr, 0)

            syms = sorted(list(eq_expr.free_symbols), key=lambda s: s.name)
            if not syms:
                if eq_expr == 0:
                    result["solution"] = "Identity: equation is always true."
                else:
                    result["solution"] = "Contradiction: equation is never true."
            else:
                sol = solve(Eq(left, right), syms[0])
                result["solution"] = sol
                result["factor"] = factor(eq_expr)
                result["expand"] = expand(eq_expr)
        else:
            expr = try_parse_expression(corrected)
            result["parsed"] = expr
            result["simplified"] = simplify(expr)
            result["factor"] = factor(expr)
            result["expand"] = expand(expr)

            if len(expr.free_symbols) == 0:
                result["solution"] = float(expr.evalf())
            else:
                syms = ", ".join(sorted([s.name for s in expr.free_symbols]))
                result["solution"] = f"Expression depends on symbols: {syms}"

    except SympifyError as e:
        result["error"] = f"Could not parse expression: {e}"
    except Exception as e:
        result["error"] = f"Error: {e}"

    return result

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Math Corrector & Solver", layout="centered")
st.title("🧮 Math Corrector & Solver")

st.write(
    """
    Enter any **math expression** or **equation**.
    The app will:
    1. ✅ Auto-correct common math typos  
    2. 🧠 Simplify and solve it  
    3. ✨ Display results beautifully using LaTeX
    """
)

input_text = st.text_area("✏️ Enter your math question here:", "2x + 3 = 7")

if st.button("Correct & Solve"):
    outcome = solve_input(input_text)

    st.subheader("Input")
    st.markdown(f"**Original:** `{outcome['original']}`")
    st.markdown(f"**Corrected:** `{outcome['corrected']}`")

    if outcome["error"]:
        st.error(outcome["error"])
    else:
        if outcome["parsed"]:
            st.subheader("Parsed / Normalized")
            st.latex(latex(outcome["parsed"]))

        if outcome["simplified"]:
            st.subheader("Simplified Form")
            st.latex(latex(outcome["simplified"]))

        if outcome["factor"] is not None:
            st.subheader("Factorized Form")
            st.latex(latex(outcome["factor"]))

        if outcome["expand"] is not None:
            st.subheader("Expanded Form")
            st.latex(latex(outcome["expand"]))

        st.subheader("✅ Solution / Evaluation")
        st.write(outcome["solution"])

st.divider()
st.write("### 💡 Try these examples:")
st.code(
    """2x + 3 = 7
x^2 - 5x + 6 = 0
sqrt(16) + 3*4
3x + 2 = 2x + 8
1,000 + 2,500
"""
)
st.caption("Built with Streamlit + SymPy — handles algebraic solving and simplification.")
