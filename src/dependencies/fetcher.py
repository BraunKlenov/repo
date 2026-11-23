import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import quote, urlsplit, urlunsplit

REQUEST_TIMEOUT = 10
USER_AGENT = "DependencyVisualizer/1.0"

REQUIREMENT_PATTERN = re.compile(
    r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)"
)

OPTIONAL_EXTRA_PATTERN = re.compile(
    r"\bextra\s*==\s*(['\"])[^'\"]+\1",
    re.IGNORECASE,
)


def fetch_metadata(repo_url):
    """Получает JSON-метаданные пакета из репозитория."""
    request = Request(
        repo_url,
        headers={"User-Agent": USER_AGENT},
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            content = response.read().decode("utf-8")
    except HTTPError as error:
        raise ValueError(
            f"Ошибка HTTP: {error.code}"
        ) from error
    except URLError as error:
        raise ValueError(
            f"Не удалось подключиться к репозиторию: {error.reason}"
        ) from error
    except TimeoutError as error:
        raise ValueError(
            "Время ожидания ответа от репозитория истекло."
        ) from error

    return parse_metadata_json(content)


def parse_metadata_json(content):
    """Преобразование ответа репозитория в JSON."""
    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Репозиторий вернул некорректный JSON."
        ) from error


def extract_direct_dependencies(metadata):
    """Извлекает прямые обязательные зависимости."""
    info = get_package_info(metadata)
    requirements = info.get("requires_dist") or []

    validate_requirements(requirements)

    return [
        requirement.strip()
        for requirement in requirements
        if is_required_dependency(requirement)
    ]


def get_package_info(metadata):
    """Получение раздела info из метаданных."""
    try:
        return metadata["info"]
    except (KeyError, TypeError) as error:
        raise ValueError(
            "В ответе отсутствует раздел info."
        ) from error


def validate_requirements(requirements):
    """Проверка формата списка зависимостей."""
    if not isinstance(requirements, list):
        raise ValueError(
            "Поле requires_dist имеет неверный формат."
        )


def is_required_dependency(requirement):
    """Проверяет, является ли зависимость обязательной."""
    if not isinstance(requirement, str):
        return False

    marker = requirement.partition(";")[2]

    if OPTIONAL_EXTRA_PATTERN.search(marker):
        return False

    if not REQUIREMENT_PATTERN.match(requirement):
        raise ValueError(
            f"Некорректная запись зависимости: {requirement}"
        )

    return True


def get_direct_dependencies(repo_url):
    """Получает список прямых зависимостей пакета."""
    metadata = fetch_metadata(repo_url)
    return extract_direct_dependencies(metadata)


def get_repository_base(repo_url):
    """Определяет базовый адрес репозитория."""
    parsed_url = urlsplit(repo_url)
    path = parsed_url.path.rstrip("/")
    parts = path.split("/")

    if len(parts) >= 2 and parts[-1] == "json":
        path = "/".join(parts[:-2])

    return urlunsplit((
        parsed_url.scheme,
        parsed_url.netloc,
        path.rstrip("/"),
        "",
        "",
    ))


def build_package_url(repo_url, package):
    """Формирует URL JSON-метаданных пакета."""
    parsed_url = urlsplit(repo_url)

    if parsed_url.scheme not in ("http", "https"):
        raise ValueError("Некорректная схема URL репозитория.")

    if not parsed_url.netloc:
        raise ValueError("Некорректный URL репозитория.")

    base_url = get_repository_base(repo_url)
    package_name = quote(package)

    return f"{base_url}/{package_name}/json"


def get_package_dependencies(package, repo_url):
    """Получает названия прямых зависимостей пакета."""
    package_url = build_package_url(repo_url, package)
    metadata = fetch_metadata(package_url)

    requirements = extract_direct_dependencies(metadata)

    return extract_package_names(requirements)


def extract_package_names(requirements):
    """Извлекает названия пакетов из требований."""
    dependencies = []

    for requirement in requirements:
        match = REQUIREMENT_PATTERN.match(requirement)

        if match:
            dependencies.append(match.group(1).lower())

    return dependencies