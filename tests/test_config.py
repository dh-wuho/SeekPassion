from pathlib import Path

from seekpassion.config import load_config

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_minimal_config(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "companies: []\n"
        "resume:\n"
        "  static_file: resume/static.yaml\n"
        "  pool_file: resume/pool.yaml\n"
    )
    cfg = load_config(cfg_file)
    assert cfg.fit_weight == 0.6
    assert cfg.success_weight == 0.4
    assert cfg.companies == []


def test_load_config_with_companies(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "companies:\n"
        "  - name: Acme\n"
        "    url: https://boards.greenhouse.io/acme\n"
        "resume:\n"
        "  static_file: resume/static.yaml\n"
        "  pool_file: resume/pool.yaml\n"
    )
    cfg = load_config(cfg_file)
    assert len(cfg.companies) == 1
    assert cfg.companies[0].name == "Acme"
