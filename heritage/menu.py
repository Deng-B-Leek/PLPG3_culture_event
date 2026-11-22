"""The menu part of the app: what the user sees and types.

HeritageCLI.run() is the main loop. It shows the menu, does what the user
picks, and shows the menu again until they choose to exit.
"""
from .errors import (
    PermissionDenied,
    RecordNotFound,
    StorageError,
    ValidationError,
)
from .roles import Permission, Role, has_permission
from .validators import (
    MAX_LONG_TEXT,
    MAX_SHORT_TEXT,
    clean_date,
    clean_text,
)

TRADITIONS = "traditions"
EVENTS = "events"

BANNER = """\
==========================================
   COMMUNITY CULTURE AND HERITAGE LOG
   Keep our traditions and events alive
=========================================="""

MENU = """
--- MAIN MENU ---
1. View records
2. Search records
3. Add a record
4. Update a record
5. Delete a record
0. Exit"""


def choose_role():
    """Ask the user for a role and return it."""
    print(BANNER)
    print("\nChoose your role:")
    roles = list(Role)
    for number, role in enumerate(roles, start=1):
        allowed = ", ".join(
            p.value for p in Permission if has_permission(role, p)
        )
        print(f"{number}. {role.value} (can {allowed})")
    while True:
        choice = input(f"Choose 1-{len(roles)}: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(roles):
            return roles[int(choice) - 1]
        print(f"  Please type a number from 1 to {len(roles)}.")


class HeritageCLI:
    def __init__(self, service):
        self.service = service

    def run(self):
        """Show the menu again and again until the user exits."""
        while True:
            print(f"\nRole: {self.service.role.value}")
            print(MENU)
            choice = self._ask_number("Choose 0-5: ", 0, 5)
            if choice == 0:
                print("\nThank you for keeping our heritage alive. Goodbye!")
                return
            try:
                if choice == 1:
                    self._view_records()
                elif choice == 2:
                    self._search_records()
                elif choice == 3:
                    self._add_record()
                elif choice == 4:
                    self._update_record()
                else:
                    self._delete_record()
            except (
                ValidationError,
                PermissionDenied,
                RecordNotFound,
                StorageError,
            ) as error:
                print(f"\n  {error}")

    def _pick_record_type(self):
        """Ask for a tradition or an event. None means the user went back."""
        print("\nWhich type of record?")
        print("1. Tradition")
        print("2. Event")
        print("0. Back")
        choice = self._ask_number("Choose 0-2: ", 0, 2)
        if choice == 1:
            return TRADITIONS
        if choice == 2:
            return EVENTS
        return None

    def _allowed(self, permission):
        """Check the role. If it is not allowed, say so and return False."""
        if has_permission(self.service.role, permission):
            return True
        print(
            f"\n  Sorry, the role '{self.service.role.value}' is not allowed "
            f"to {permission.value} records."
        )
        print("  Restart the program and choose another role to do this.")
        return False

    def _view_records(self):
        table = self._pick_record_type()
        if table is None:
            return
        records = self._get_all(table)
        self._show_table(table, records)
        if not records:
            return
        record_id = input(
            "Type an ID to see the whole record (Enter to go back): "
        ).strip()
        if record_id:
            self._show_record(self.service.get_record(table, record_id))

    def _search_records(self):
        table = self._pick_record_type()
        if table is None:
            return
        keyword = input("Search for: ").strip()
        if not keyword:
            print("  Please type something to search for.")
            return
        self._show_table(table, self._get_all(table, keyword))

    def _add_record(self):
        # check the role first, before asking anything
        if not self._allowed(Permission.CREATE):
            return
        table = self._pick_record_type()
        if table is None:
            return
        if table == TRADITIONS:
            name = self._ask_text("Tradition name: ", "Tradition name")
            community = self._ask_text("Community: ", "Community")
            description = self._ask_text(
                "Description: ", "Description", MAX_LONG_TEXT
            )
            new_id = self.service.add_tradition(name, community, description)
        else:
            event_name = self._ask_text("Event name: ", "Event name")
            event_date = self._ask_date("Event date (YYYY-MM-DD): ")
            location = self._ask_text("Location: ", "Location")
            new_id = self.service.add_event(event_name, event_date, location)
        print(f"  Saved! The new record has ID {new_id}.")

    def _update_record(self):
        # check the role first, before asking anything
        if not self._allowed(Permission.UPDATE):
            return
        table = self._pick_record_type()
        if table is None:
            return
        record = self._ask_existing_record(table, "update")
        if record is None:
            return
        print("Press Enter to keep the current value.")
        if table == TRADITIONS:
            name = self._ask_text(
                f"Tradition name [{record['name']}]: ",
                "Tradition name",
                keep=record["name"],
            )
            community = self._ask_text(
                f"Community [{record['community']}]: ",
                "Community",
                keep=record["community"],
            )
            description = self._ask_text(
                f"Description [{record['description']}]: ",
                "Description",
                MAX_LONG_TEXT,
                keep=record["description"],
            )
            self.service.update_tradition(
                record["id"], name, community, description
            )
        else:
            event_name = self._ask_text(
                f"Event name [{record['event_name']}]: ",
                "Event name",
                keep=record["event_name"],
            )
            event_date = self._ask_date(
                f"Event date [{record['event_date']}]: ",
                keep=record["event_date"],
            )
            location = self._ask_text(
                f"Location [{record['location']}]: ",
                "Location",
                keep=record["location"],
            )
            self.service.update_event(
                record["id"], event_name, event_date, location
            )
        print(f"  Updated record {record['id']}.")

    def _delete_record(self):
        # check the role first, before asking anything
        if not self._allowed(Permission.DELETE):
            return
        table = self._pick_record_type()
        if table is None:
            return
        record = self._ask_existing_record(table, "delete")
        if record is None:
            return
        title = record.get("name") or record.get("event_name")
        answer = input(f"Delete '{title}' for good? Type yes to confirm: ")
        if answer.strip().lower() != "yes":
            print("  Cancelled. Nothing was deleted.")
            return
        self.service.delete_record(table, record["id"])
        print(f"  Deleted record {record['id']}.")

    def _get_all(self, table, keyword=None):
        if table == TRADITIONS:
            return self.service.list_traditions(keyword)
        return self.service.list_events(keyword)

    def _ask_existing_record(self, table, action):
        """Show the records, ask for an ID and return that record."""
        records = self._get_all(table)
        if not records:
            print("  There are no records of this type yet.")
            return None
        self._show_table(table, records)
        record_id = input(
            f"ID of the record to {action} (Enter to cancel): "
        ).strip()
        if not record_id:
            return None
        return self.service.get_record(table, record_id)

    def _ask_number(self, prompt, low, high):
        """Ask until the user types a whole number from low to high."""
        while True:
            raw = input(prompt).strip()
            if raw.isdigit() and low <= int(raw) <= high:
                return int(raw)
            print(f"  Please type a number from {low} to {high}.")

    def _ask_text(self, prompt, field, max_length=MAX_SHORT_TEXT, keep=None):
        """Ask until the text is accepted. Enter keeps the old value."""
        while True:
            raw = input(prompt)
            if keep is not None and not raw.strip():
                return keep
            try:
                return clean_text(raw, field, max_length)
            except ValidationError as error:
                print(f"  {error}")

    def _ask_date(self, prompt, keep=None):
        """Ask until the date is accepted. Enter keeps the old value."""
        while True:
            raw = input(prompt)
            if keep is not None and not raw.strip():
                return keep
            try:
                return clean_date(raw)
            except ValidationError as error:
                print(f"  {error}")

    def _show_table(self, table, records):
        if not records:
            print("\n  No records found.")
            return
        if table == TRADITIONS:
            print(f"\n{'ID':<4} {'Name':<30} {'Community':<25}")
            for r in records:
                print(
                    f"{r['id']:<4} {_cut(r['name'], 30):<30} "
                    f"{_cut(r['community'], 25):<25}"
                )
        else:
            print(f"\n{'ID':<4} {'Date':<11} {'Event':<28} {'Location':<22}")
            for r in records:
                print(
                    f"{r['id']:<4} {r['event_date']:<11} "
                    f"{_cut(r['event_name'], 28):<28} "
                    f"{_cut(r['location'], 22):<22}"
                )
        print(f"({len(records)} found)")

    def _show_record(self, record):
        print(f"\n--- Record {record['id']} ---")
        for key, value in record.items():
            if key != "id":
                print(f"{key.replace('_', ' ').capitalize():<12}: {value}")


def _cut(text, width):
    """Cut long text so it fits in a table column."""
    text = str(text)
    return text if len(text) <= width else text[: width - 3] + "..."
