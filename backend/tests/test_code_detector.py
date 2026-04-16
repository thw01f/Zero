"""Tests for language auto-detector."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.code_detector import detect_language

def test_detects_python_import():
    assert detect_language("import os\nprint('hi')") == 'python'

def test_detects_javascript_const():
    assert detect_language("const x = 1;\nconsole.log(x)") == 'javascript'

def test_detects_typescript_interface():
    assert detect_language("interface User { name: string; age: number }") == 'typescript'

def test_detects_java_main():
    assert detect_language("public static void main(String[] args) {}") == 'java'

def test_detects_bash_shebang():
    assert detect_language("#!/bin/bash\necho hello") == 'bash'

def test_returns_none_for_unknown():
    assert detect_language("???  ~~~  ###") is None
