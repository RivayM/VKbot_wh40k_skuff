# database/__init__.py

from database import tournament_db
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
    reset_monthly_amounts,   # <-- добавить
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

# Импорты из tournament_db.py (новый модуль)
# database/__init__.py

from database.tournament_db import (
    init_tournament_tables,
    get_or_create_player,
    get_player_armies,
    add_army,
    update_army_stats,
    create_tournament,
    get_all_tournaments,
    get_tournament,
    update_tournament,
    delete_tournament,
    register_for_tournament,
    get_registrations,
    get_registration_by_user,
    is_registered,
    update_registration_roster,
    add_payment,
    get_pending_payments,
    approve_payment,
    reject_payment,
    create_match,
    get_matches_by_round,
    get_match,
    update_match_result,
    get_leaderboard,
    get_registration_by_id
)

__all__ = [
    'get_connection', 'close_connection',
    'init_sponsors_table', 'is_sponsor', 'add_sponsor', 'remove_sponsor',
    'get_all_sponsors', 'get_sponsor', 'get_sponsor_days', 'update_payment_date',
    'add_waiting_for_name', 'remove_waiting_for_name', 'is_waiting_for_name',
    'add_waiting_for_photo', 'remove_waiting_for_photo', 'is_waiting_for_photo',
    'add_waiting_for_unsubscribe', 'remove_waiting_for_unsubscribe', 'is_waiting_for_unsubscribe',
    'init_key_table', 'take_key', 'return_key', 'get_key_holder', 'has_key',
    'init_tournament_tables',
    'get_or_create_player', 'get_player_armies', 'add_army', 'update_army_stats',
    'create_tournament', 'get_all_tournaments', 'get_tournament', 'update_tournament',
    'delete_tournament', 'register_for_tournament', 'get_registrations',
    'get_registration_by_user', 'is_registered', 'update_registration_roster',
    'add_payment', 'get_pending_payments', 'approve_payment', 'reject_payment',
    'create_match', 'get_matches_by_round', 'get_match', 'update_match_result',
    'get_leaderboard', 'get_registration_by_id',
]