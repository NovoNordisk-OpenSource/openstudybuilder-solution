import sys

from sblint.sblinter import SBLinter

if __name__ == "__main__":
    SBLinter.validate_and_report(sys.argv[1:], SBLinter.get_sblinters())
