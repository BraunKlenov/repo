
import os
import subprocess
from pathlib import Path


MERMAID_HEADER = "flowchart TD"
MERMAID_EXTENSION = ".mmd"
PUPPETEER_CONFIG = "puppeteer-config.json"
MERMAID_PACKAGE = "@mermaid-js/mermaid-cli"


def escape_label(label):
    """Экранирует специальные символы в подписи узла."""
    return (
        str(label)
        .replace("&", "&amp;")
        .replace('"', "#quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", " ")
    )


def collect_packages(graph):
    """Собирает все уникальные пакеты из графа."""
    packages = list(graph)

    for dependencies in graph.values():
        for dependency in dependencies:
            if dependency not in packages:
                packages.append(dependency)

    return packages


def create_identifiers(packages):
    """Создаёт идентификаторы Mermaid для пакетов."""
    return {
        package: f"node_{index}"
        for index, package in enumerate(packages)
    }


def add_mermaid_nodes(lines, packages, identifiers):
    """Добавляет узлы графа в Mermaid."""
    for package in packages:
        node_id = identifiers[package]
        label = escape_label(package)
        lines.append(f'    {node_id}["{label}"]')


def add_mermaid_edges(lines, graph, identifiers):
    """Добавляет связи между узлами Mermaid."""
    for package, dependencies in graph.items():
        source = identifiers[package]

        for dependency in dependencies:
            target = identifiers[dependency]
            lines.append(f"    {source} --> {target}")


def build_mermaid(graph):
    """Преобразует граф зависимостей в текст Mermaid."""
    packages = collect_packages(graph)
    identifiers = create_identifiers(packages)

    lines = [MERMAID_HEADER]

    add_mermaid_nodes(lines, packages, identifiers)
    add_mermaid_edges(lines, graph, identifiers)

    return "\n".join(lines) + "\n"


def validate_puppeteer_config(config_path):
    """Проверяет наличие конфигурации Puppeteer."""
    if not config_path.is_file():
        raise ValueError(
            f"Файл конфигурации Puppeteer не найден: {config_path}"
        )


def save_mermaid_file(graph, mermaid_path):
    """Сохраняет граф в Mermaid-файл."""
    mermaid_path.write_text(
        build_mermaid(graph),
        encoding="utf-8"
    )


def create_mermaid_command(mermaid_path, output, config_path):
    """Создаёт команду запуска Mermaid CLI."""
    return [
        "npx",
        "--yes",
        "--package",
        MERMAID_PACKAGE,
        "mmdc",
        "-i",
        str(mermaid_path),
        "-o",
        str(output),
        "-p",
        str(config_path.resolve())
    ]


def run_mermaid_command(command):
    """Запускает Mermaid CLI."""
    try:
        if os.name == "nt":
            subprocess.run(
                ["cmd", "/c", *command],
                check=True
            )
        else:
            subprocess.run(command, check=True)

    except FileNotFoundError as error:
        raise ValueError(
            "Не удалось найти npx. Проверь установку Node.js."
        ) from error

    except subprocess.CalledProcessError as error:
        raise ValueError(
            "Не удалось создать изображение Mermaid."
        ) from error


def generate_png(graph, output_path):
    """Сохраняет Mermaid-файл и генерирует изображение PNG."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    mermaid_path = output.with_suffix(MERMAID_EXTENSION)
    config_path = Path(PUPPETEER_CONFIG)

    validate_puppeteer_config(config_path)
    save_mermaid_file(graph, mermaid_path)

    command = create_mermaid_command(
        mermaid_path,
        output,
        config_path
    )

    run_mermaid_command(command)
