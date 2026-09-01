"""
Testy skryptow importu danych (import_excel.py, import_svhc.py).

Skrypty byly zepsute: pobieraly `ExcelSourceSubstance` / `SVHCSubstance`
z modulu `app`, a te klasy sa w `models`. Kazde uruchomienie konczylo sie
ImportError, wiec udokumentowana procedura importu CLP/SVHC nie dzialala
w ogole - ani przy instalacji recznej, ani w kontenerze. Zaden test tego
nie wykrywal, bo skrypty sa uruchamiane wylacznie z linii polecen.

Test nie wykonuje importu danych (to wymaga bazy i pliku Excel) - sprawdza
tylko, ze wszystkie nazwy, ktore skrypty importuja, faktycznie istnieja
w modulach, z ktorych sa brane.
"""
import ast
import importlib
import io
import pathlib

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ('import_excel.py', 'import_svhc.py')


def _module_level_from_imports(path):
    """Zwraca [(modul, [nazwy...])] dla instrukcji `from X import ...`."""
    tree = ast.parse(io.open(path, encoding='utf-8').read(), filename=str(path))
    found = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append((node.module, [alias.name for alias in node.names]))
    return found


@pytest.mark.parametrize('script', SCRIPTS)
def test_script_exists(script):
    assert (PROJECT_ROOT / script).is_file(), f"brak skryptu {script}"


@pytest.mark.parametrize('script', SCRIPTS)
def test_imported_names_actually_exist(script):
    """
    Regresja: `from app import ExcelSourceSubstance` przechodzi statyczna
    inspekcje, ale wywala sie przy uruchomieniu. Sprawdzamy realnie.
    """
    imports = _module_level_from_imports(PROJECT_ROOT / script)
    assert imports, f"{script} nie ma zadnych importow - podejrzane"

    for module_name, names in imports:
        if module_name in ('pandas',):
            continue
        module = importlib.import_module(module_name)
        for name in names:
            assert hasattr(module, name), (
                f"{script}: '{name}' nie istnieje w module '{module_name}'"
            )


@pytest.mark.parametrize('script', SCRIPTS)
def test_script_compiles(script):
    source = io.open(PROJECT_ROOT / script, encoding='utf-8').read()
    compile(source, str(PROJECT_ROOT / script), 'exec')
