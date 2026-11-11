"""Initial payment evidence schema."""
from alembic import op
from app.db import Base
from app import models
revision='0001'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    Base.metadata.create_all(op.get_bind())
    if op.get_bind().dialect.name=='sqlite':
        for action in ('UPDATE','DELETE'):
            op.execute(f"CREATE TRIGGER recorder_no_{action.lower()} BEFORE {action} ON flight_recorder_events BEGIN SELECT RAISE(ABORT, 'append-only recorder'); END")
    elif op.get_bind().dialect.name=='postgresql':
        op.execute("CREATE FUNCTION reject_recorder_mutation() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'append-only recorder'; END; $$")
        op.execute('CREATE TRIGGER recorder_immutable BEFORE UPDATE OR DELETE ON flight_recorder_events FOR EACH ROW EXECUTE FUNCTION reject_recorder_mutation()')
def downgrade():raise RuntimeError('Destructive evidence downgrade disabled; restore backup')
