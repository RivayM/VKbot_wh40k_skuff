# database/__init__.py

from database.db_manager import get_connection, close_connection

# Импорты из sponsors_db.py
from database.sponsors_db import (
    init_sponsors_table,
    is_sponsor,
    add_sponsor,
    remove_sponsor,
    get_all_sponsors,
    get_sponsor,
    get_sponsor_days,
    update_payment_date,
    add_waiting_for_name,
    remove_waiting_for_name,
    is_waiting_for_name,
    add_waiting_for_photo,
    remove_waiting_for_photo,
    is_waiting_for_photo,
    add_waiting_for_unsubscribe,
    remove_waiting_for_unsubscribe,
    is_waiting_for_unsubscribe
)

# Импорты из key_db.py
from database.key_db import (
    init_key_table,
    take_key,
    return_key,
    get_key_holder,
    has_key
)

# Импорты из tournaments_db.py
from database.tournaments_db import (
    init_tournaments_table,
    create_tournament,
    get_active_tournaments,
    get_all_tournaments,
    get_tournament,
    register_for_tournament,
    get_tournament_registrations,
    is_registered_for_tournament,
    start_tournament,
    complete_tournament,
    get_active_tournament
)

__all__ = [
    # db_manager
    'get_connection',
    'close_connection',
    # sponsors_db
    'init_sponsors_table',
    'is_sponsor',
    'add_sponsor',
    'remove_sponsor',
    'get_all_sponsors',
    'get_sponsor',
    'get_sponsor_days',
    'update_payment_date',
    'add_waiting_for_name',
    'remove_waiting_for_name',
    'is_waiting_for_name',
    'add_waiting_for_photo',
    'remove_waiting_for_photo',
    'is_waiting_for_photo',
    'add_waiting_for_unsubscribe',
    'remove_waiting_for_unsubscribe',
    'is_waiting_for_unsubscribe',
    # key_db
    'init_key_table',
    'take_key',
    'return_key',
    'get_key_holder',
    'has_key',
    # tournaments_db
    'init_tournaments_table',
    'create_tournament',
    'get_active_tournaments',
    'get_all_tournaments',
    'get_tournament',
    'register_for_tournament',
    'get_tournament_registrations',
    'is_registered_for_tournament',
    'start_tournament',
    'complete_tournament',
    'get_active_tournament'
]