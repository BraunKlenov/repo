
import sys
from pathlib import Path

from src.config.config import parse_config
from src.dependencies.fetcher import get_package_dependencies
from src.dependencies.graph import (
    build_dependency_graph,
    invert_dependency_graph,
)
from src.dependencies.test_repository import load_test_repository
from src.vizualization.mermaid import generate_png


def print_graph(graph):
    """Выводит построенный граф зависимостей."""
    print("\nГраф зависимостей:")

    for package, dependencies in graph.items():
        dependency_list = ", ".join(dependencies)
        print(f"{package} -> {dependency_list or 'нет зависимостей'}")


def print_cycles(cycles):
    """Выводит найденные циклические зависимости."""
    print("\nЦиклические зависимости:")

    if not cycles:
        print("Циклы не обнаружены.")
        return

    for cycle in cycles:
        print(" -> ".join(cycle))


def print_ascii_tree(root_package, graph):
    """Выводит граф зависимостей в виде ASCII-дерева."""

    def print_branch(package, prefix, is_last, active_path):
        branch = "\\-- " if is_last else "|-- "
        print(prefix + branch + package)

        if package in active_path:
            return

        dependencies = graph.get(package, [])
        next_prefix = prefix + ("    " if is_last else "|   ")
        next_path = active_path + [package]

        for index, dependency in enumerate(dependencies):
            is_last_dependency = index == len(dependencies) - 1

            if dependency in next_path:
                cycle_branch = (
                    "\\-- " if is_last_dependency else "|-- "
                )
                print(
                    next_prefix
                    + cycle_branch
                    + dependency
                    + " (cycle)"
                )
                continue

            print_branch(
                dependency,
                next_prefix,
                is_last_dependency,
                next_path,
            )

    print("\nДерево зависимостей:")
    print(root_package)

    dependencies = graph.get(root_package, [])

    for index, dependency in enumerate(dependencies):
        print_branch(
            dependency,
            "",
            index == len(dependencies) - 1,
            [root_package],
        )



def create_test_dependency_provider(config):
    """Создаёт источник зависимостей для тестового репозитория."""
    repository = load_test_repository(config.repo)

    if config.reverse:
        if config.package not in repository:
            raise ValueError(
                f"Пакет {config.package} отсутствует в репозитории."
            )

        return invert_dependency_graph(repository).get

    return repository.get


def create_dependency_provider(config):
    """Создаёт источник зависимостей для обхода графа."""
    if config.test_mode:
        return create_test_dependency_provider(config)

    if config.reverse:
        raise ValueError(
            "Обратные зависимости доступны только в тестовом режиме."
        )

    def provider(package):
        return get_package_dependencies(package, config.repo)

    return provider


def build_graph(config, dependency_provider):
    """Строит граф зависимостей и находит циклы."""
    return build_dependency_graph(
        config.package,
        dependency_provider,
        config.max_depth,
    )


def print_graph_results(graph, cycles, config):
    """Выводит результаты построения графа."""
    if config.reverse:
        print("\nРежим: обратные зависимости")

    print_graph(graph)
    print_cycles(cycles)
    print(f"\nВсего пакетов в графе: {len(graph)}")

    if config.ascii:
        print_ascii_tree(config.package, graph)


def save_graph(graph, config):
    """Сохраняет граф в PNG и Mermaid."""
    generate_png(graph, config.output)

    output_path = Path(config.output)
    mermaid_path = output_path.with_suffix(".mmd")

    print(f"\nMermaid-файл сохранён: {mermaid_path}")
    print(f"Изображение PNG сохранено: {output_path}")


def main():
    """Запускает построение и визуализацию графа зависимостей."""
    config = parse_config()

    try:
        dependency_provider = create_dependency_provider(config)
        graph, cycles = build_graph(config, dependency_provider)

        print_graph_results(graph, cycles, config)
        save_graph(graph, config)

    except ValueError as error:
        print(f"\nОшибка: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
