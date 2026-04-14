from __future__ import annotations

import io
import re
from dataclasses import dataclass
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


ATTACKER_ROLES = {"A", "ATT", "ATTACCANTE"}


@dataclass(frozen=True)
class DownloadedSheet:
    source_id: str
    raw_bytes: bytes
    source_url: str


class FantacalcioClient:
    def __init__(self, votes_page_url: str, timeout: int = 20, cookie_header: str | None = None) -> None:
        self._votes_page_url = votes_page_url
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": self._votes_page_url,
            }
        )
        if cookie_header:
            self._session.headers.update({"Cookie": cookie_header})

    def download_available_votes_sheets(self) -> list[DownloadedSheet]:
        page_response = self._session.get(self._votes_page_url, timeout=self._timeout)
        page_response.raise_for_status()

        sheet_urls = self._extract_sheet_urls(page_response.text)
        if not sheet_urls:
            raise RuntimeError(
                "Nessun file voti trovato nella pagina. "
                "Il sito potrebbe richiedere autenticazione Fantacalcio."
            )

        sheets: list[DownloadedSheet] = []
        for sheet_url in sheet_urls:
            file_response = self._session.get(sheet_url, timeout=self._timeout)
            if file_response.status_code == 401:
                raise RuntimeError(
                    "Download voti non autorizzato (HTTP 401). "
                    "Imposta FANTACALCIO_COOKIE nel file .env con il cookie della tua sessione login."
                )
            file_response.raise_for_status()

            source_id = self._extract_source_id(sheet_url, file_response.content)
            sheets.append(
                DownloadedSheet(
                    source_id=source_id,
                    raw_bytes=file_response.content,
                    source_url=sheet_url,
                )
            )

        return sorted(sheets, key=_sort_key_for_source)

    def _extract_sheet_urls(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        candidates: list[str] = []
        seen: set[str] = set()
        api_candidates: list[tuple[int, int]] = []

        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"]).strip()
            api_match = re.search(r"/api/v1/excel/votes/(\d+)/(\d+)", href, re.IGNORECASE)
            if api_match:
                season_id, giornata = api_match.groups()
                api_candidates.append((int(season_id), int(giornata)))

            if ".xlsx" in href.lower() or api_match:
                normalized = urljoin(self._votes_page_url, href)
                if normalized not in seen:
                    seen.add(normalized)
                    candidates.append(normalized)

        if api_candidates:
            season_id, current_giornata = max(api_candidates, key=lambda item: item[1])
            for giornata in range(1, current_giornata + 1):
                api_url = urljoin(self._votes_page_url, f"/api/v1/Excel/votes/{season_id}/{giornata}")
                if api_url not in seen:
                    seen.add(api_url)
                    candidates.append(api_url)

        return candidates

    def _extract_source_id(self, url: str, content: bytes) -> str:
        # We prefer an ID derived from the filename. If it is missing, fallback to content length.
        api_match = re.search(r"/api/v1/excel/votes/(\d+)/(\d+)", url, re.IGNORECASE)
        if api_match:
            season_id, giornata = api_match.groups()
            return f"season-{season_id}-giornata-{giornata}"

        filename = url.rsplit("/", 1)[-1]
        match = re.search(r"([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{8}|giornata[-_ ]?[0-9]+)", filename, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return f"{filename}:{len(content)}"


def extract_trunk_players(xlsx_bytes: bytes) -> list[str]:
    raw = pd.read_excel(io.BytesIO(xlsx_bytes), header=None)

    role_idx: int | None = None
    name_idx: int | None = None
    vote_idx: int | None = None

    for _, row in raw.iterrows():
        normalized = [str(value).strip().lower() for value in row.tolist()]
        candidate_role = _pick_index(normalized, ["r", "ruolo"])
        candidate_name = _pick_index(normalized, ["nome", "giocatore", "calciatore"])
        candidate_vote = _pick_index(normalized, ["voto"])

        # Header must contain all required labels in the same row.
        if candidate_role is not None and candidate_name is not None and candidate_vote is not None:
            role_idx = candidate_role
            name_idx = candidate_name
            vote_idx = candidate_vote
            break

    if role_idx is None or name_idx is None or vote_idx is None:
        raise RuntimeError("Impossibile individuare le colonne ruolo/nome/voto nel file voti.")

    trunk_players: list[str] = []
    for _, row in raw.iterrows():
        role_raw = str(row.iloc[role_idx]).strip().upper()
        name_raw = str(row.iloc[name_idx]).strip()
        vote_raw = str(row.iloc[vote_idx]).strip().replace(",", ".")

        if not role_raw or role_raw == "NAN" or role_raw in {"R", "RUOLO"}:
            continue
        if not name_raw or name_raw.lower() in {"nan", "nome", "giocatore", "calciatore"}:
            continue

        match = re.search(r"([0-9]+(?:\.[0-9]+)?)", vote_raw)
        if not match:
            continue
        vote = float(match.group(1))

        if role_raw in ATTACKER_ROLES and vote <= 5:
            trunk_players.append(name_raw)

    return trunk_players


def _pick_index(values: list[str], candidates: list[str]) -> int | None:
    for index, value in enumerate(values):
        if value in candidates:
            return index
    for index, value in enumerate(values):
        if any(candidate in value for candidate in candidates):
            return index
    return None


def _sort_key_for_source(sheet: DownloadedSheet) -> tuple[int, str]:
    match = re.search(r"giornata[-_ ]?([0-9]+)", sheet.source_id, re.IGNORECASE)
    if match:
        return int(match.group(1)), sheet.source_id
    return 10_000, sheet.source_id
