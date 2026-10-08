import requests


GITHUB_API = "https://api.github.com/search/repositories"
PYPI_API = "https://pypi.org/pypi/{}/json"


def search_github(query: str, limit: int = 5):
    try:
        response = requests.get(
            GITHUB_API,
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": limit,
            },
            timeout=15,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Mafia-Tool-Manager",
            },
        )

        response.raise_for_status()

        results = []

        for item in response.json().get("items", []):
            results.append({
                "name": item.get("name"),
                "full_name": item.get("full_name"),
                "description": item.get("description") or "",
                "url": item.get("html_url"),
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language") or "unknown",
            })

        return results

    except Exception as exc:
        return [{
            "error": str(exc)
        }]


def search_pypi(package: str):
    try:
        response = requests.get(
            PYPI_API.format(package),
            timeout=15,
            headers={
                "User-Agent": "Mafia-Tool-Manager",
            },
        )

        if response.status_code != 200:
            return None

        data = response.json()

        return {
            "name": data["info"]["name"],
            "version": data["info"]["version"],
            "summary": data["info"].get("summary") or "",
            "url": data["info"].get("home_page") or "",
        }

    except Exception:
        return None
