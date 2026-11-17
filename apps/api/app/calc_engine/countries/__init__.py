from .ae import UaeRulePack
from .base import CountryRulePack, UnsupportedCountryError
from .de import GermanyRulePack

_PACKS: dict[str, CountryRulePack] = {
    "DE": GermanyRulePack(),
    "AE": UaeRulePack(),
}


def get_rule_pack(country_code: str) -> CountryRulePack:
    """No fallback: an unsupported country is an error, never another country's rules."""
    try:
        return _PACKS[country_code.upper()]
    except KeyError:
        raise UnsupportedCountryError(f"no rule pack for country {country_code!r}") from None


def supported_countries() -> list[str]:
    return sorted(_PACKS)


__all__ = ["CountryRulePack", "UnsupportedCountryError", "get_rule_pack", "supported_countries"]
