"""Seed PostgreSQL with common components. Run after pg_schema.sql."""
SEED_COMPONENTS = [
    {
        "lib_id": "MCU_ST_STM32F405RGTx",
        "name": "STM32F405RGTx",
        "mpn": "STM32F405RGTx",
        "category": "MCU",
        "manufacturer": "STMicroelectronics",
        "package": "LQFP64",
        "jlc_part": "C12345",
        "price": 18.20,
        "description": "STM32F405, 32-bit ARM Cortex-M4, 168MHz, 1MB Flash, 64-pin LQFP, 3.3V"
    },
    {
        "lib_id": "POWER_5V_LM1117",
        "name": "LM1117-5.0",
        "mpn": "LM1117-5.0",
        "category": "POWER",
        "manufacturer": "Texas Instruments",
        "package": "SOT-223",
        "jlc_part": "C12346",
        "price": 0.85,
        "description": "LM1117 5V LDO voltage regulator, 800mA output, 1.2V drop"
    },
    {
        "lib_id": "POWER_3V3_LM1117",
        "name": "LM1117-3.3",
        "mpn": "LM1117-3.3",
        "category": "POWER",
        "manufacturer": "Texas Instruments",
        "package": "SOT-223",
        "jlc_part": "C12347",
        "price": 0.85,
        "description": "LM1117 3.3V LDO voltage regulator, 800mA output"
    },
    {
        "lib_id": "CONNECTOR_USB_TYPEC",
        "name": "USB Type-C",
        "mpn": "USB Type-C",
        "category": "CONNECTOR",
        "manufacturer": "Various",
        "package": "SMD",
        "jlc_part": "C12348",
        "price": 0.50,
        "description": "USB Type-C connector, 24-pin, for power delivery and data"
    },
    {
        "lib_id": "CRYSTAL_8MHz",
        "name": "8MHz Crystal",
        "mpn": "ABM8G-8.000MHz",
        "category": "CRYSTAL",
        "manufacturer": "Abracon",
        "package": "HC49",
        "jlc_part": "C12349",
        "price": 0.35,
        "description": "8MHz crystal oscillator, 20ppm, HC49 SMD package"
    },
    # Add more common components here...
]

def main():
    from backend.db.pg_vector_store import add_component
    for comp in SEED_COMPONENTS:
        try:
            add_component(comp)
            print(f"Added: {comp['lib_id']}")
        except Exception as e:
            print(f"Failed to add {comp['lib_id']}: {e}")

if __name__ == "__main__":
    main()