# app.py
import streamlit as st
from sympy import sympify, Eq, solve, symbols, simplify, factor, expand, SympifyError
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

# Helpers
TRANSFORMS = (standard_transformations + (implicit_multiplication_application,))

COMMON_REPLACEMENTS = {
    '×': '*',
    '✕': '*',
    '·': '*',
    '÷': '/',
    '∕': '/',
    '^': '**',          # caret -> power
    '—': '-',           # em dash -> minus
    '–': '-',           # en dash -> minus
    '−': '-',           # minus sign
    'sqrt': 'sqrt',     # keep - sympy supports sqrt
}

def clean_input(s: str) -> str:
    """Apply simple corrections to common OCR/typing mistakes."""
    if s is None:
        return ''
    s = s.strip()
    for k, v in COMMON_REPLACEMENTS.items():
        s = s.replace(k, v)
    # Remove accidental commas from large numbers like 1,000 -> 1000
    s = s.replace(',', '')
    # Normalize spaces around = and operators for easier parsing / display
    s = s.replace(' = ', '=').replace(' =', '=').replace('= ', '=')
    return s

def try_parse_expression(expr_text: str):
    """Return a SymPy expression if possible, else raise."""
    # try sympify/parse_expr (with implicit multiplication allowed)
    return parse_expr(expr_text, transformations=TRANSFORMS)

def solve_input(text: str):
    corrected = clean_input(text)
    result = {
        'original': text,
        'corrected': corrected,
        'parsed': None,
        'simplified': None,
        'factor': None,
        'expand': None,
        'solution': None,
        'error': None,
    }

    # Determine if it's an equation (contains '='). If so, solve; else evaluate/simplify.
    try:
        if '=' in corrected:
            left_s, right_s = corrected.split('=', 1)
            left = try_parse_expression(left_s)
            right = try_parse_expression(right_s)
            result['parsed'] = f"{left} = {right}"

            # Move all to one side
            eq_expr = simplify(left - right)
            result['simplified'] = f"{eq_expr} = 0"

            # Try to infer symbol(s) to solve for
            syms = sorted(list(eq_expr.free_symbols), key=lambda s: s.name)
            if not syms:
                # No symbol — maybe it's an identity or contradiction
                if eq_expr == 0:
                    result['solution'] = "Identity: equation is always true."
                else:
                    result['solution'] = "Contradiction: equation is never true."
            else:
                # Solve for each symbol (show primary)
                primary = syms[0]
                sol = solve(Eq(left, right), primary)
                result['solution'] = sol
                # Also give factor/expand if useful
                try:
                    result['factor'] = factor(eq_expr)
                    result['expand'] = expand(eq_expr)
                except Exception:
                    result['factor'] = None
                    result['expand'] = None
        else:
            # Expression (not an equation)
            expr = try_parse_expression(corrected)
            result['parsed'] = str(expr)
            try:
                result['simplified'] = str(simplify(expr))
            except Exception:
                result['simplified'] = None
            try:
                # Try numeric evaluation if expression is numeric (no free symbols)
                if len(expr.free_symbols) == 0:
                    result['solution'] = float(expr.evalf())
                else:
                    result['solution'] = f"Expression depends on symbols: {', '.join(sorted([s.name for s in expr.free_symbols]))}"
            except Exception as e:
                result['solution'] = f"Could not evaluate numerically: {e}"
            try:
                result['factor'] = str(factor(expr))
                result['expand'] = str(expand(expr))
            except Exception:
                result['factor'] = None
                result['expand'] = None

    except SympifyError as e:
        result['error'] = f"Could not parse expression: {e}"
    except Exception as e:
        result['error'] = f"Error during processing: {e}"

    return result

# Streamlit UI
st.set_page_config(page_title="Math Corrector & Solver", layout="centered")
st.title("Math Corrector & Solver")
st.write("Paste a math expression or equation. The app will attempt to *correct common typos*, parse it with SymPy, and show the cleaned expression plus a worked solution / steps.")

input_text = st.text_area("Enter math expression or equation", value="2x + 3 = 7")
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Correct & Solve"):
        outcome = solve_input(input_text)

        st.subheader("Input")
        st.markdown(f"**Original:** `{outcome['original']}`")
        st.markdown(f"**Corrected:** `{outcome['corrected']}`")

        if outcome['error']:
            st.error(outcome['error'])
        else:
            if outcome['parsed']:
                st.subheader("Parsed / Normalized")
                st.code(outcome['parsed'])

            if outcome['simplified']:
                st.subheader("Simplified (moved to one side if equation)")
                st.code(outcome['simplified'])

            if outcome.get('factor'):
                st.subheader("Factor (if applicable)")
                st.code(str(outcome['factor']))

            if outcome.get('expand'):
                st.subheader("Expand (if applicable)")
                st.code(str(outcome['expand']))

            st.subheader("Solution / Evaluation")
            st.write(outcome['solution'])

            st.subheader("Notes")
            st.write("""
            - This tool handles symbolic algebraic expressions and equations (e.g. `2*x + 3 = 7`, `x^2 - 4`).
            - Common fixes: `^` -> power, `×` -> `*`, `÷` -> `/`, removes commas in numbers.
            - For word problems or natural-language math (e.g. "If John has..."), the app might not understand — try to convert the problem into symbols first.
            - If multiple variables exist, the app shows a solution for the primary variable (alphabetically) when possible.
            """)

with col2:
    st.subheader("Examples you can try")
    st.markdown("""
    - `2x + 3 = 7`
    - `x^2 - 5x + 6 = 0`
    - `sqrt(16) + 3*4`
    - `3x + 2 = 2x + 8`
    - `1,000 + 2,500` (commas handled)
    - `2*(x + 1) = 8`
    """)

st.caption("Built with Streamlit + SymPy — works best for algebraic expressions/equations. For more advanced step-by-step arithmetic proofs, consider pairing with a CAS step-by-step engine.")
