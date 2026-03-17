#!/usr/bin/env python3
"""Conversor de configuración HPE OfficeConnect 1920S -> Aruba Instant On 1960.

El objetivo es acelerar una migración inicial. El archivo resultante siempre
requiere validación manual antes de aplicarlo en producción.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConversionResult:
    output_lines: list[str]
    converted: int
    omitted: int
    untouched: int
    warnings: list[str]


class ConfigConverter:
    def __init__(self, target_slot: int = 1) -> None:
        self.target_slot = target_slot

        self.omit_patterns = [
            re.compile(r"^\s*undo\b", re.IGNORECASE),
            re.compile(r"^\s*snmp-agent\b", re.IGNORECASE),
            re.compile(r"^\s*user-interface\b", re.IGNORECASE),
            re.compile(r"^\s*ip\s+http\b", re.IGNORECASE),
            re.compile(r"^\s*line\s+(vty|console)\b", re.IGNORECASE),
        ]

        self.rewriters = [
            (re.compile(r"^\s*sysname\s+(.+)$", re.IGNORECASE), self._rewrite_sysname),
            (
                re.compile(
                    r"^(\s*interface\s+)(gigabitethernet|ten-gigabitethernet)(\d+)/(\d+)/(\d+)(.*)$",
                    re.IGNORECASE,
                ),
                self._rewrite_interface,
            ),
            (
                re.compile(r"^(\s*dhcp\s+server\s+enable)\s*$", re.IGNORECASE),
                self._rewrite_dhcp_enable,
            ),
        ]

    def convert(self, raw_config: str) -> ConversionResult:
        output: list[str] = []
        converted = omitted = untouched = 0
        warnings: list[str] = []

        output.append("! ---------------------------------------------------------------------")
        output.append("! Archivo generado automáticamente por convert_1920s_to_1960s.py")
        output.append("! Revise manualmente sintaxis, ACLs, PoE, routing, seguridad y SNMP.")
        output.append("! ---------------------------------------------------------------------")

        for line in raw_config.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                output.append(line)
                untouched += 1
                continue

            omitted_line = False
            for pattern in self.omit_patterns:
                if pattern.search(line):
                    output.append(f"! OMITIDO (revisar equivalente ArubaOS-Switch): {line}")
                    omitted += 1
                    omitted_line = True
                    break

            if omitted_line:
                continue

            rewritten = None
            for pattern, handler in self.rewriters:
                match = pattern.match(line)
                if match:
                    rewritten = handler(match)
                    break

            if rewritten is None:
                output.append(line)
                untouched += 1
            else:
                output.append(rewritten)
                converted += 1

                if rewritten.lower().startswith("interface ") and "/0/" in line:
                    warnings.append(
                        f"Interfaz convertida desde formato x/0/y -> x/{self.target_slot}/y: '{line.strip()}'"
                    )

        return ConversionResult(output, converted, omitted, untouched, warnings)

    @staticmethod
    def _rewrite_sysname(match: re.Match[str]) -> str:
        name = match.group(1).strip()
        return f"hostname {name}"

    def _rewrite_interface(self, match: re.Match[str]) -> str:
        prefix = match.group(1)
        iface_type = match.group(2).lower()
        stack_id = match.group(3)
        _source_slot = match.group(4)
        port = match.group(5)
        suffix = match.group(6)

        return f"{prefix}{iface_type} {stack_id}/{self.target_slot}/{port}{suffix}".rstrip()

    @staticmethod
    def _rewrite_dhcp_enable(_match: re.Match[str]) -> str:
        return "dhcp-server enable"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convierte una configuración base de HPE OfficeConnect 1920S "
            "a un formato inicial compatible con Aruba Instant On 1960."
        )
    )
    parser.add_argument("input", type=Path, help="Archivo de configuración origen (1920S)")
    parser.add_argument("output", type=Path, help="Archivo de configuración destino (1960)")
    parser.add_argument(
        "--target-slot",
        type=int,
        default=1,
        help="Valor de slot para interfaces de salida (default: 1)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Ruta opcional para guardar reporte de cambios",
    )
    return parser.parse_args()


def write_report(path: Path, result: ConversionResult) -> None:
    lines = [
        "Reporte de conversión 1920S -> 1960",
        f"Líneas convertidas: {result.converted}",
        f"Líneas omitidas: {result.omitted}",
        f"Líneas sin cambios: {result.untouched}",
        "",
        "Advertencias:",
    ]
    if result.warnings:
        lines.extend(f"- {w}" for w in result.warnings)
    else:
        lines.append("- Sin advertencias específicas")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()

    source_text = args.input.read_text(encoding="utf-8", errors="ignore")
    converter = ConfigConverter(target_slot=args.target_slot)
    result = converter.convert(source_text)

    args.output.write_text("\n".join(result.output_lines) + "\n", encoding="utf-8")

    print(f"Conversión finalizada: {args.input} -> {args.output}")
    print(f"  Convertidas : {result.converted}")
    print(f"  Omitidas    : {result.omitted}")
    print(f"  Sin cambios : {result.untouched}")

    if args.report:
        write_report(args.report, result)
        print(f"Reporte guardado en: {args.report}")


if __name__ == "__main__":
    main()
