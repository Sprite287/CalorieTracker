"""Add missing columns to existing tables

Revision ID: b23af7e857f9
Revises: a12af7e857f9
Create Date: 2025-08-07 13:45:00.024602

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
import uuid


# revision identifiers, used by Alembic.
revision = 'b23af7e857f9'
down_revision = 'a12af7e857f9'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to existing tables if they don't exist."""
    
    # Get database inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if profiles table exists
    if 'profiles' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('profiles')]
        
        # Add uuid column if missing
        if 'uuid' not in columns:
            # Add column as nullable first
            op.add_column('profiles', sa.Column('uuid', sa.String(), nullable=True))
            
            # Generate UUIDs for existing rows
            profiles_table = sa.table('profiles',
                sa.column('profile_name', sa.String),
                sa.column('uuid', sa.String)
            )
            
            # Get all profiles
            result = conn.execute(sa.select([profiles_table.c.profile_name]))
            for row in result:
                profile_uuid = str(uuid.uuid4())
                conn.execute(
                    profiles_table.update()
                    .where(profiles_table.c.profile_name == row[0])
                    .values(uuid=profile_uuid)
                )
            
            # Now make it non-nullable and unique
            with op.batch_alter_table('profiles') as batch_op:
                batch_op.alter_column('uuid', nullable=False)
                batch_op.create_unique_constraint('uq_profiles_uuid', ['uuid'])
        
        # Add created_at column if missing
        if 'created_at' not in columns:
            op.add_column('profiles', sa.Column('created_at', sa.DateTime(), 
                                               server_default=sa.func.now(), nullable=True))
    
    # Check if weekly_log table exists
    if 'weekly_log' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('weekly_log')]
        
        # Add created_at column if missing
        if 'created_at' not in columns:
            op.add_column('weekly_log', sa.Column('created_at', sa.DateTime(), 
                                                 server_default=sa.func.now(), nullable=True))
        
        # Check for indexes
        indexes = inspector.get_indexes('weekly_log')
        index_names = [idx['name'] for idx in indexes]
        
        # Add missing indexes
        if 'idx_profile_date' not in index_names:
            with op.batch_alter_table('weekly_log') as batch_op:
                batch_op.create_index('idx_profile_date', ['profile_name', 'date'], unique=False)
        
        if 'ix_weekly_log_date' not in index_names:
            with op.batch_alter_table('weekly_log') as batch_op:
                batch_op.create_index('ix_weekly_log_date', ['date'], unique=False)


def downgrade():
    """Remove added columns and indexes."""
    
    # Remove indexes from weekly_log
    with op.batch_alter_table('weekly_log') as batch_op:
        try:
            batch_op.drop_index('ix_weekly_log_date')
        except:
            pass
        try:
            batch_op.drop_index('idx_profile_date')
        except:
            pass
    
    # Remove created_at from weekly_log
    try:
        op.drop_column('weekly_log', 'created_at')
    except:
        pass
    
    # Remove columns from profiles
    try:
        with op.batch_alter_table('profiles') as batch_op:
            batch_op.drop_constraint('uq_profiles_uuid', type_='unique')
        op.drop_column('profiles', 'created_at')
        op.drop_column('profiles', 'uuid')
    except:
        pass