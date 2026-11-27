
import json
import re
from pathlib import Path


PACKAGE_PATTERN = re.compile(r"[A-Z]+")


def validate_graph_structure(graph):
    """Проверяет общую структуру графа."""
    if not isinstance(graph, dict) or not graph:
        raise ValueError(
            "Граф должен быть непустым JSON-объектом."
        )


def validate_package_name(package):
    """Проверяет название пакета."""
    if not isinstance(package, str):
        raise ValueError(
            "Название пакета должно быть строкой."
        )

    if not PACKAGE_PATTERN.fullmatch(package):
        raise ValueError(
            f"Недопустимое название пакета: {package}"
        )


def validate_dependency_list(package, dependencies):
    """Проверяет список зависимостей пакета."""
    if not isinstance(dependencies, list):
        raise ValueError(
            f"Зависимости пакета {package} должны быть списком."
        )


def validate_dependency_name(dependency, graph):
    """Проверяет название и наличие зависимости."""
    if not isinstance(dependency, str):
        raise ValueError(
            f"Недопустимая зависимость: {dependency}"
        )

    if not PACKAGE_PATTERN.fullmatch(dependency):
        raise ValueError(
            f"Недопустимая зависимость: {dependency}"
        )

    if dependency not in graph:
        raise ValueError(
            f"Пакет {dependency} отсутствует в описании графа."
        )


def validate_package_dependencies(package, dependencies, graph):
    """Проверяет все зависимости одного пакета."""
    validate_dependency_list(package, dependencies)

    for dependency in dependencies:
        validate_dependency_name(dependency, graph)


def validate_test_graph(graph):
    """Проверяет структуру и содержимое тестового графа."""
    validate_graph_structure(graph)

    for package, dependencies in graph.items():
        validate_package_name(package)
        validate_package_dependencies(
            package,
            dependencies,
            graph
        )

    return graph


def read_repository(file_path):
    """Читает JSON-файл тестового репозитория."""
    try:
        with Path(file_path).open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            "Файл тестового репозитория содержит некорректный JSON."
        ) from error

    except OSError as error:
        raise ValueError(
            f"Не удалось прочитать файл: {file_path}"
        ) from error


def load_test_repository(file_path):
    """Загружает и проверяет тестовый граф из JSON-файла."""
    graph = read_repository(file_path)
    return validate_test_graph(graph)
