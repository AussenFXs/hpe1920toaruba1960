# Conversor 1920S -> Aruba Instant On 1960

Script para convertir de forma **inicial** un archivo de configuración de:

- HPE OfficeConnect 1920S (JL381A)

hacia una versión base compatible con:

- HPE Aruba Instant On 1960S (JL806A)

## Uso

```bash
python3 convert_1920s_to_1960s.py config_1920s.txt config_1960s.txt --report reporte.txt
```

### Parámetros

Se utiliza automáticamente la plantilla base `template_1960s_base.cfg` (si existe en el mismo directorio del script).

- `input`: archivo de configuración de origen.
- `output`: archivo convertido.
- `--target-slot`: slot destino para interfaces al convertir `x/0/y` a `x/<slot>/y` (por defecto `1`).
- `--report`: archivo opcional de reporte.

## Qué transforma

- `sysname <NOMBRE>` -> `hostname <NOMBRE>`
- `interface gigabitethernet|ten-gigabitethernet x/0/y` -> `interface ... x/1/y` (o slot definido)
- `dhcp server enable` -> `dhcp-server enable`

## Qué marca como omitido (requiere revisión manual)

- Líneas `undo ...`
- `snmp-agent ...`
- `user-interface ...`
- `ip http ...`
- `line vty|console ...`

## Importante

La conversión **no es 100% automática**. Siempre valida:

- VLANs, trunks/LAG, ACLs
- políticas de seguridad
- SNMP, AAA/usuarios, gestión remota
- funcionalidades específicas del modelo (PoE, routing, QoS)
