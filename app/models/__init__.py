# Import all models here so SQLAlchemy registers them
# and all relationships resolve correctly at startup.
from app.models.user       import User, UserRole        # noqa: F401
from app.models.otp        import OTPRecord             # noqa: F401
from app.models.audit_log  import AuditLog              # noqa: F401
from app.models.property   import Property, Occupant    # noqa: F401
from app.models.bill       import Bill, BillStatus      # noqa: F401
from app.models.payment    import Payment               # noqa: F401
from app.models.complaint  import Complaint             # noqa: F401
from app.models.notice     import Notice                # noqa: F401
from app.models.setting    import Setting               # noqa: F401
