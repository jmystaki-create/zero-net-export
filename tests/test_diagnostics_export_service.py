from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"


class DiagnosticsExportServiceTests(unittest.TestCase):
    def test_service_module_defines_logger_used_by_handlers(self) -> None:
        source = (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")

        self.assertIn("import logging", source)
        self.assertIn("_LOGGER = logging.getLogger(__name__)", source)
        self.assertIn('_LOGGER.info("Diagnostics exported to %s", filename)', source)
        self.assertIn('_LOGGER.info("Repairs issues cleared for Zero Net Export entry %s", entry.entry_id)', source)

    def test_diagnostics_export_writes_file_off_event_loop(self) -> None:
        source = (PACKAGE_ROOT / "coordinator.py").read_text(encoding="utf-8")
        export_block = source.split("async def async_export_diagnostics", 1)[1].split(
            "async def async_note_current_integration_version", 1
        )[0]

        self.assertIn("await hass.async_add_executor_job(_write_diagnostics_file)", export_block)
        self.assertIn("json.dump(diagnostics, f, indent=2, default=str)", export_block)
        self.assertNotIn("\n        with open(filepath", export_block)


if __name__ == "__main__":
    unittest.main()
