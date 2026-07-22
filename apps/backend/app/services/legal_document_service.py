from dataclasses import dataclass

from app.core.config import settings
from app.core.roles import UserRole


CURRENT_LEGAL_VERSION = "2026-07-21"
CURRENT_LEGAL_EFFECTIVE_DATE = "21 July 2026"


@dataclass(frozen=True)
class LegalDocument:
    slug: str
    title: str
    roles: frozenset[str]

    @property
    def url(self) -> str:
        base = settings.legal_public_base_url.rstrip("/")
        return f"{base}/{self.slug}/{CURRENT_LEGAL_VERSION}"


LEGAL_DOCUMENTS = (
    LegalDocument(
        slug="privacy",
        title="Privacy Notice",
        roles=frozenset((UserRole.CLIENT.value, UserRole.WORKER.value)),
    ),
    LegalDocument(
        slug="client-terms",
        title="Client Terms",
        roles=frozenset((UserRole.CLIENT.value,)),
    ),
    LegalDocument(
        slug="worker-terms",
        title="Worker Terms",
        roles=frozenset((UserRole.WORKER.value,)),
    ),
    LegalDocument(
        slug="refund-cancellation",
        title="Refund and Cancellation Policy",
        roles=frozenset((UserRole.CLIENT.value,)),
    ),
    LegalDocument(
        slug="grievance",
        title="Grievance Process",
        roles=frozenset((UserRole.CLIENT.value, UserRole.WORKER.value)),
    ),
)


def required_documents_for_role(role: str) -> tuple[LegalDocument, ...]:
    return tuple(document for document in LEGAL_DOCUMENTS if role in document.roles)

