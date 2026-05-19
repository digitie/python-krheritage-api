from __future__ import annotations

from krheritage.codes import KoglLicense


def is_ai_trainable(license_value: KoglLicense | int | None) -> bool:
    if license_value is None:
        return False
    license_ = (
        license_value if isinstance(license_value, KoglLicense) else KoglLicense(license_value)
    )
    return license_.allows_ai_training
