# NOVA - space rogue-lite for NumWorks
.PHONY: all build test lint mem balance shots clean

all: lint build test mem

build:
	python3 tools/build.py

test:
	python3 tests/run_all.py

mem:
	python3 tools/memcheck.py

balance:
	python3 tests/test_balance.py

lint:
	python3 tools/lint_globals.py src/nova*.py
	python3 tools/fiximports.py

shots:
	python3 tools/screenshot.py

clean:
	rm -rf tests/__pycache__ tools/__pycache__ tools/emu/__pycache__ tools/mp/work
