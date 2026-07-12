from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    one_c_base_url: str
    one_c_host_header: str | None
    forms_path: str
    counterparties_path: str
    timeout_seconds: int
    kafka_bootstrap_servers: str
    ownership_topic: str
    counterparties_topic: str

    @classmethod
    def from_env(cls) -> "Settings":
        base_url = os.environ["ONE_C_BASE_URL"].rstrip("/")
        host_header = os.getenv("ONE_C_HOST_HEADER", "").strip() or None
        return cls(
            one_c_base_url=base_url,
            one_c_host_header=host_header,
            forms_path=os.getenv("ONE_C_FORMS_PATH", "forms-ownership").lstrip("/"),
            counterparties_path=os.getenv("ONE_C_COUNTERPARTIES_PATH", "counterparties").lstrip("/"),
            timeout_seconds=int(os.getenv("ONE_C_TIMEOUT_SECONDS", "15")),
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            ownership_topic=os.getenv("KAFKA_OWNERSHIP_TOPIC", "1c.ownership_forms.v1"),
            counterparties_topic=os.getenv("KAFKA_COUNTERPARTIES_TOPIC", "1c.counterparties.v1"),
        )
