from datetime import datetime, date, timedelta
from typing import Union
from pyparsing import (
    Literal,
    Group,
    Forward,
    Regex,
    ParseException,
    CaselessKeyword,
    Suppress,
    delimitedList,
)
import math
import operator
from dataclasses import dataclass


expr_stack = []

def push_first(toks):
    expr_stack.append(toks[0])

bnf = None

def BNF():
    """
    addop   :: '+' | '-'
    integer :: ['+' | '-'] '0'..'9'+
    atom    :: real | fn '(' expr ')' | '(' expr ')'
    factor  :: atom [ expop factor ]*
    term    :: factor [ multop factor ]*
    expr    :: term [ addop term ]*
    """
    global bnf
    if not bnf:
        now = CaselessKeyword('now')
        # fnumber = Combine(Word("+-"+nums, nums) +
        #                    Optional("." + Optional(Word(nums))) +
        #                    Optional(e + Word("+-"+nums, nums)))
        # or use provided pyparsing_common.number, but convert back to str:
        # fnumber = ppc.number().addParseAction(lambda t: str(t[0]))    
        date = Regex(r"(?:\d+[年])*(?:\d{1,2}[月])*(?:\d{1,2}[日])*")
        
        # fnumber = Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
        # ident = Word(alphas, alphanums + "_$")

        plus, minus, mult, div = map(Literal, "+-*/")
        lpar, rpar = map(Suppress, "()")
        addop = plus | minus
        multop = mult | div

        expr = Forward()
        expr_list = delimitedList(Group(expr))
        # add parse action that replaces the function identifier with a (name, number of args) tuple
        def insert_fn_argcount_tuple(t):
            fn = t.pop(0)
            num_args = len(t[0])
            t.insert(0, (fn, num_args))

        atom = (
            addop[...]
            + (
                # (now | fnumber | ident).setParseAction(push_first)
                (now | date).setParseAction(push_first)
                | Group(lpar + expr + rpar)
            )
        )

        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left
        # exponents, instead of left-to-right that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        term = atom + (multop + atom).setParseAction(push_first)[...]
        expr <<= term + (addop + term).setParseAction(push_first)[...]
        bnf = expr
    return bnf


# map operator symbols to corresponding arithmetic operations
epsilon = 1e-12
opn = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}

@dataclass
class YearMonthDay:
    year: int = 0
    month: int = 0
    day: int = 0
    
    def to_approx_days(self) -> int:
        return self.year * 365 + self.month * 30 + self.day
    
    def to_timedelta(self):
        return timedelta(days=self.to_approx_days())

import re
YEARMONTHDAY_PATTERN = re.compile(r'(?:(?P<year>\d+)年)*(?:(?P<month>\d+)月)*((?P<day>\d+)日)*')

def str_to_ymd(string: str) -> YearMonthDay:
    return YearMonthDay(**{k: int(v) if v else 0 for k, v in YEARMONTHDAY_PATTERN.match(string).groupdict().items()})

def to_datetime(input_date: Union[str, datetime]) -> datetime:
    if isinstance(input_date, datetime):
        return input_date
    return datetime.strptime(input_date, "%Y年%m月%d日")    

def evaluate_stack(s):
    op, num_args = s.pop(), 0
    if isinstance(op, tuple):
        op, num_args = op
    elif op == "-":
        op2 = evaluate_stack(s)
        op1 = evaluate_stack(s)
        return op1 if isinstance(op1, datetime) else to_datetime(op1) - to_datetime(op2)
    elif op == "+":
        op2 = evaluate_stack(s)
        op1 = evaluate_stack(s)
        return to_datetime(op1) + str_to_ymd(op2).to_timedelta()
    elif op == "now":
        return datetime.now().timestamp
    else:
        # try to evaluate as int first, then as float if int fails
        return op
        # try:
        #     return int(op)
        # except ValueError:
        #     return float(op)

def evaluate(equation: str) -> Union[datetime, timedelta]:    
    BNF().parseString(equation, parseAll=True)
    val = evaluate_stack(expr_stack[:])
    
    return val

if __name__ == "__main__":
    def test(s, expected):
        expr_stack[:] = []
        try:
            results = BNF().parseString(s, parseAll=True)
            val = evaluate_stack(expr_stack[:])
        except ParseException as pe:
            print(s, "failed parse:", str(pe))
            raise pe
        except Exception as e:
            print(s, "failed eval:", str(e), expr_stack)
            raise e
        else:
            if val == expected:
                print(s, "=", val, results, "=>", expr_stack)
            else:
                print(s + "!!!", val, "!=", expected, results, "=>", expr_stack)

    test("2020年9月8日 - 2020年3月4日", date(2020, 9, 8) - date(2020,3,4))
    test("2013年9月8日 - 2014年3月4日", date(2013, 9, 8) - date(2014,3,4))
    test("2020年9月8日 + 2020年9月4日", date(2020, 9, 8))
    test("2020年9月8日 + 4日", date(2020, 9, 8))
    test("2020年9月8日 + 4日 - 3日", date(2020, 9, 8))
