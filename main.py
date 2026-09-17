import calendar
import re

from playwright.sync_api import sync_playwright


# ============================================================
# SEARCH SETTINGS
# ============================================================

FROM_CITY = "Dhaka"
TO_CITY = "Rajshahi"

YEAR = 2026
MONTH = 9
DAY = 20

SEARCH_CLASS = "SHOVAN"

# Number of seats to select.
# Maximum allowed: 4
SEAT_COUNT = 3


# ============================================================
# VALIDATE SETTINGS
# ============================================================

if not 1 <= SEAT_COUNT <= 4:
    raise ValueError("SEAT_COUNT must be between 1 and 4.")


# ============================================================
# HELPERS
# ============================================================


def normalize_text(text):
    return " ".join(text.split())


# ============================================================
# ACCEPT DISCLAIMER
# ============================================================


def accept_disclaimer(page):

    try:
        agree_button = page.get_by_role(
            "button",
            name=re.compile(r"I\s*AGREE", re.IGNORECASE)
        ).first

        if agree_button.count() > 0 and agree_button.is_visible():

            print("Disclaimer found. Clicking I AGREE...")

            agree_button.click(timeout=5000)

            page.wait_for_timeout(500)

            print("Disclaimer accepted.")

        else:

            print("No disclaimer found.")

    except Exception:

        print("No disclaimer found.")


# ============================================================
# WAIT FOR LOGIN IF REQUIRED
# ============================================================


def wait_for_login(page):

    print("\nChecking login status...")

    page.wait_for_timeout(1500)

    login_indicators = page.locator(
        "input[type='password']:visible, "
        "input[name='password']:visible, "
        "input[placeholder*='Password']:visible"
    )

    if login_indicators.count() == 0:

        print("Already logged in.")

        return

    print("\n================================================")
    print("LOGIN REQUIRED")
    print("================================================")
    print("Please log in manually in the browser.")
    print("The script will continue automatically after login.")

    try:

        login_indicators.first.wait_for(
            state="hidden",
            timeout=300000
        )

    except Exception:

        pass

    page.wait_for_timeout(2000)

    print("Login completed. Continuing...")


# ============================================================
# STATION SELECTION
# ============================================================


def select_station(page, field_selector, station_name):

    field = page.locator(field_selector)

    field.click()

    page.wait_for_timeout(300)

    field.fill(station_name)

    page.wait_for_timeout(1000)

    elements = page.get_by_text(
        station_name,
        exact=True
    )

    target = None

    for i in range(elements.count()):

        element = elements.nth(i)

        if element.is_visible():

            target = element

    if target is None:

        raise RuntimeError(
            f"Could not find '{station_name}' suggestion. "
            f"This route is not available in Railway at this moment."
        )

    target.click()

    page.wait_for_timeout(500)

    print(
        f"Station selected: {field.input_value()}"
    )


# ============================================================
# DATE SELECTION
# ============================================================


def select_date(page, year, month, day):

    date_field = page.locator("#doj")

    date_field.click()

    page.wait_for_timeout(300)

    datepicker = page.locator(
        ".ui-datepicker:visible"
    )

    current_month_year = normalize_text(
        datepicker.locator(
            ".ui-datepicker-title"
        ).inner_text()
    )

    target_month_year = (
        f"{calendar.month_name[month]} {year}"
    )

    print(
        "Available month:",
        current_month_year
    )

    print(
        "Requested month:",
        target_month_year
    )

    if current_month_year != target_month_year:

        raise ValueError(
            f"Requested {target_month_year}, "
            f"but Railway currently shows "
            f"{current_month_year}."
        )

    day_links = datepicker.locator(
        "td:not(.ui-datepicker-other-month) a"
    )

    for i in range(day_links.count()):

        link = day_links.nth(i)

        if link.inner_text().strip() == str(day):

            link.click()

            print(
                f"Selected date: "
                f"{year}-{month:02d}-{day:02d}"
            )

            return

    raise ValueError(
        f"Day {day} is not available."
    )


# ============================================================
# FIND TRAIN CONTAINERS
# ============================================================


def discover_train_containers(page):

    candidates = page.locator(
        "div:has(.trip-details-btn)"
    )

    containers = []

    for i in range(candidates.count()):

        candidate = candidates.nth(i)

        if not candidate.is_visible():

            continue

        if candidate.locator(
            ".seat-classes-row"
        ).count() == 0:

            continue

        parent_count = candidate.locator(
            "xpath=ancestor::div[.//div[contains(@class,'trip-details-btn')]]"
        ).count()

        if parent_count > 0:

            continue

        containers.append(candidate)

    return containers


# ============================================================
# GET TRAIN NAME
# ============================================================


def get_train_name(train_container):

    text = normalize_text(
        train_container.inner_text()
    )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines:

        if re.search(r"\(\d+\)", line):

            return line

    return "Unknown train"


# ============================================================
# CLICK TRAIN / OPEN CLASSES
# ============================================================


def open_train(page, train_container):

    print("\nClicking train...")

    details_button = train_container.locator(
        ".trip-details-btn"
    ).first

    if details_button.count() == 0:

        print(
            "Train details button not found."
        )

        return False

    if not details_button.is_visible():

        print(
            "Train details button is not visible."
        )

        return False

    print(
        "Clicking train details button..."
    )

    details_button.click(force=True)

    page.wait_for_timeout(1000)

    try:

        train_container.locator(
            ".single-seat-class:visible"
        ).first.wait_for(
            state="visible",
            timeout=5000
        )

    except Exception:

        page.wait_for_timeout(1500)

    class_count = train_container.locator(
        ".single-seat-class:visible"
    ).count()

    print(
        "Visible classes:",
        class_count
    )

    return class_count > 0


# ============================================================
# DISCOVER CLASS ROWS
# ============================================================


def discover_class_rows(train_container):

    rows = train_container.locator(
        ".single-seat-class:visible"
    )

    result = []

    for i in range(rows.count()):

        row = rows.nth(i)

        if row.is_visible():

            result.append(row)

    return result


# ============================================================
# GET CLASS INFORMATION
# ============================================================


def get_class_information(class_row):

    class_name = "Unknown"

    class_name_locator = class_row.locator(
        ".seat-class-name"
    )

    if class_name_locator.count() > 0:

        try:

            class_name = normalize_text(
                class_name_locator.first.inner_text()
            )

        except Exception:

            pass

    availability = None

    availability_locator = class_row.locator(
        ".all-seats"
    )

    if availability_locator.count() > 0:

        try:

            availability_text = normalize_text(
                availability_locator.first.inner_text()
            )

            match = re.search(
                r"\d+",
                availability_text
            )

            if match:

                availability = int(
                    match.group()
                )

        except Exception:

            pass

    return class_name, availability


# ============================================================
# CLICK BOOK NOW
# ============================================================


def click_book_now(page, class_row):

    print(
        "\nSearching for BOOK NOW button..."
    )

    button = class_row.get_by_role(
        "button",
        name=re.compile(
            r"BOOK NOW",
            re.IGNORECASE
        )
    ).first

    if button.count() == 0:

        print(
            "BOOK NOW button not found."
        )

        return False

    if not button.is_visible():

        print(
            "BOOK NOW button is not visible."
        )

        return False

    if button.is_disabled():

        print(
            "BOOK NOW button is disabled."
        )

        return False

    print("BOOK NOW found.")

    button.scroll_into_view_if_needed()

    page.wait_for_timeout(300)

    print("Clicking BOOK NOW...")

    try:

        button.click(timeout=5000)

    except Exception as e:

        print(
            "Normal click failed:",
            e
        )

        print(
            "Trying DOM click..."
        )

        button.evaluate(
            "(element) => element.click()"
        )

    page.wait_for_timeout(3000)

    return True


# ============================================================
# CHECK WHETHER SEAT IS AVAILABLE
# ============================================================


def is_seat_available(seat):

    classes = (
        seat.get_attribute("class")
        or ""
    ).lower()

    unavailable_states = [
        "booked",
        "seat-booked",
        "seat-in-progress",
        "unavailable",
        "disabled",
        "selected",
    ]

    for state in unavailable_states:

        if state in classes:

            return False

    try:

        if seat.is_disabled():

            return False

    except Exception:

        pass

    return True


# ============================================================
# GET SEAT IDENTIFIER
# ============================================================


def get_seat_number(seat, seat_index):

    title = (
        seat.get_attribute("title")
        or ""
    )

    data_seat = (
        seat.get_attribute("data-seat")
        or ""
    )

    text = normalize_text(
        seat.inner_text()
    )

    return (
        title.strip()
        or data_seat.strip()
        or text
        or f"seat-{seat_index + 1}"
    )


# ============================================================
# CHECK CURRENT COACH
# ============================================================


def check_current_coach(page, seats_needed):

    print(
        "\nChecking current coach seat layout..."
    )

    try:

        page.locator(
            ".seat-layout-view:visible"
        ).wait_for(
            state="visible",
            timeout=15000
        )

    except Exception:

        print(
            "Seat layout did not appear."
        )

        return 0

    page.wait_for_timeout(700)

    seats = page.locator(
        ".seat-layout-view:visible "
        "button.btn-seat:visible"
    )

    seat_count = seats.count()

    print(
        "Seat icons found:",
        seat_count
    )

    if seat_count == 0:

        print(
            "No seat icons found."
        )

        return 0

    selected_count = 0

    for seat_index in range(seat_count):

        if selected_count >= seats_needed:

            break

        seat = seats.nth(seat_index)

        classes = (
            seat.get_attribute("class")
            or ""
        )

        seat_number = get_seat_number(
            seat,
            seat_index
        )

        print(
            f"Seat {seat_index + 1}: "
            f"{seat_number} | "
            f"class: {classes}"
        )

        if not is_seat_available(seat):

            continue

        print(
            "\nAVAILABLE SEAT FOUND!"
        )

        print(
            "Seat:",
            seat_number
        )

        print(
            "Clicking seat..."
        )

        seat.scroll_into_view_if_needed()

        page.wait_for_timeout(200)

        try:

            seat.click(force=True)

        except Exception as e:

            print(
                "Seat click failed:",
                e
            )

            continue

        page.wait_for_timeout(500)

        selected_count += 1

        print(
            f"Seat selected: "
            f"{seat_number}"
        )

        print(
            f"Seats selected in this coach: "
            f"{selected_count}/{seats_needed}"
        )

    return selected_count


# ============================================================
# GET ALL COACHES WITH AVAILABLE TICKETS
# ============================================================


def discover_available_coaches(page):

    coach_select = page.locator(
        "#select-bogie:visible"
    ).first

    if coach_select.count() == 0:

        print(
            "Select Coach field not found."
        )

        return []

    options = coach_select.locator(
        "option"
    )

    coaches = []

    print(
        "\n================================================"
    )

    print(
        "DISCOVERING COACHES"
    )

    print(
        "================================================"
    )

    for i in range(options.count()):

        option = options.nth(i)

        coach_text = normalize_text(
            option.inner_text()
        )

        coach_value = (
            option.get_attribute("value")
            or ""
        )

        match = re.search(
            r"(\d+)\s*Seat\(s\)",
            coach_text,
            re.IGNORECASE
        )

        if not match:

            print(
                f"Coach option ignored: "
                f"{coach_text}"
            )

            continue

        seat_count = int(
            match.group(1)
        )

        coach_name = re.sub(
            r"\s*-\s*\d+\s*Seat\(s\).*",
            "",
            coach_text,
            flags=re.IGNORECASE
        ).strip()

        print(
            f"{coach_name}: "
            f"{seat_count} seat(s)"
        )

        if seat_count <= 0:

            continue

        coaches.append(
            {
                "name": coach_name,
                "value": coach_value,
                "seat_count": seat_count,
            }
        )

    return coaches


# ============================================================
# SELECT COACH
# ============================================================


def select_coach(page, coach):

    coach_select = page.locator(
        "#select-bogie:visible"
    ).first

    if coach_select.count() == 0:

        print(
            "Select Coach field not found."
        )

        return False

    print(
        f"\nSelecting coach: "
        f"{coach['name']}"
    )

    try:

        coach_select.select_option(
            coach["value"]
        )

    except Exception as e:

        print(
            "Could not select coach:",
            e
        )

        return False

    page.wait_for_timeout(1000)

    return True


# ============================================================
# CHECK ALL COACHES
# ============================================================


def check_all_coaches_in_class(
    page,
    required_seats
):

    coaches = discover_available_coaches(
        page
    )

    if not coaches:

        print(
            "\nNo coaches with available "
            "tickets were found."
        )

        return 0

    print(
        f"\nCoaches to check: "
        f"{len(coaches)}"
    )

    total_selected = 0

    for coach_index, coach in enumerate(
        coaches,
        start=1
    ):

        if total_selected >= required_seats:

            break

        seats_needed = (
            required_seats - total_selected
        )

        print(
            "\n================================================"
        )

        print(
            f"COACH "
            f"{coach_index}/"
            f"{len(coaches)}"
        )

        print(
            "================================================"
        )

        print(
            "Coach:",
            coach["name"]
        )

        print(
            "Reported seats:",
            coach["seat_count"]
        )

        print(
            "Seats still needed:",
            seats_needed
        )

        selected = select_coach(
            page,
            coach
        )

        if not selected:

            print(
                "Could not select this coach."
            )

            continue

        selected_in_coach = check_current_coach(
            page,
            seats_needed
        )

        total_selected += selected_in_coach

        print(
            f"\nTotal seats selected: "
            f"{total_selected}/{required_seats}"
        )

        if total_selected >= required_seats:

            print(
                "\nRequired number of seats selected."
            )

            return total_selected

        print(
            f"\nNo more required seats "
            f"found in coach {coach['name']}."
        )

    print(
        "\n================================================"
    )

    print(
        "ALL AVAILABLE COACHES CHECKED"
    )

    print(
        f"Seats selected: "
        f"{total_selected}/{required_seats}"
    )

    print(
        "================================================"
    )

    return total_selected


# ============================================================
# MAIN
# ============================================================


with sync_playwright() as p:

    browser = p.chromium.connect_over_cdp(
        "http://127.0.0.1:9222"
    )

    context = browser.contexts[0]

    if not context.pages:

        raise RuntimeError(
            "No browser page found."
        )

    page = context.pages[0]

    accept_disclaimer(page)

    print(
        "Connected to:",
        page.url
    )

    # ========================================================
    # SEARCH DETAILS
    # ========================================================

    select_station(
        page,
        "#dest_from",
        FROM_CITY
    )

    select_station(
        page,
        "#dest_to",
        TO_CITY
    )

    select_date(
        page,
        year=YEAR,
        month=MONTH,
        day=DAY
    )

    # ========================================================
    # SEARCH CLASS
    # ========================================================

    class_select = page.locator(
        "#choose_class"
    )

    class_select.select_option(
        SEARCH_CLASS
    )

    print(
        "Search class:",
        class_select.input_value()
    )

    print(
        "Requested seats:",
        SEAT_COUNT
    )

    # ========================================================
    # SEARCH TRAINS
    # ========================================================

    print(
        "\nClicking SEARCH TRAINS..."
    )

    page.get_by_role(
        "button",
        name="SEARCH TRAINS"
    ).click()

    page.wait_for_timeout(1500)

    wait_for_login(page)

    page.wait_for_timeout(5000)

    print(
        "\nSearch results loaded."
    )

    # ========================================================
    # FIND TRAINS
    # ========================================================

    train_containers = (
        discover_train_containers(page)
    )

    print(
        "\n================================================"
    )

    print(
        "TRAINS FOUND:",
        len(train_containers)
    )

    print(
        "================================================"
    )

    if not train_containers:

        raise RuntimeError(
            "No train containers were discovered."
        )

    # ========================================================
    # PROCESS TRAINS
    # ========================================================

    seat_selected = False

    selected_seat_total = 0

    train_index = 0

    while train_index < len(
        train_containers
    ):

        train_container = (
            train_containers[train_index]
        )

        train_index += 1

        print(
            "\n================================================"
        )

        print(
            f"EXPRESS "
            f"{train_index}/"
            f"{len(train_containers)}"
        )

        print(
            "================================================"
        )

        train_name = get_train_name(
            train_container
        )

        print(
            "Train:",
            train_name
        )

        # ----------------------------------------------------
        # OPEN TRAIN
        # ----------------------------------------------------

        opened = open_train(
            page,
            train_container
        )

        if not opened:

            print(
                "Could not open this train."
            )

            continue

        # ----------------------------------------------------
        # GET CLASSES
        # ----------------------------------------------------

        class_rows = discover_class_rows(
            train_container
        )

        print(
            "Classes found:",
            len(class_rows)
        )

        # ----------------------------------------------------
        # CHECK CLASSES
        # ----------------------------------------------------

        class_index = 0

        while class_index < len(
            class_rows
        ):

            class_row = class_rows[
                class_index
            ]

            class_index += 1

            class_name, availability = (
                get_class_information(
                    class_row
                )
            )

            print(
                f"\nClass {class_index}:",
                class_name
            )

            print(
                "Available tickets:",
                availability
            )

            # ------------------------------------------------
            # ZERO TICKETS
            # ------------------------------------------------

            if (
                availability is not None
                and availability <= 0
            ):

                print(
                    "No tickets. "
                    "Skipping class."
                )

                continue

            # ------------------------------------------------
            # UNKNOWN AVAILABILITY
            # ------------------------------------------------

            if availability is None:

                print(
                    "Availability unknown. "
                    "Skipping class."
                )

                continue

            # ------------------------------------------------
            # AVAILABLE CLASS
            # ------------------------------------------------

            print(
                "\nAVAILABLE CLASS FOUND!"
            )

            print(
                "Train:",
                train_name
            )

            print(
                "Class:",
                class_name
            )

            print(
                "Available tickets:",
                availability
            )

            print(
                "Seats requested:",
                SEAT_COUNT
            )

            # ------------------------------------------------
            # CHECK WHETHER CLASS CAN SATISFY REQUEST
            # ------------------------------------------------

            if availability < SEAT_COUNT:

                print(
                    f"Only {availability} ticket(s) "
                    f"available. "
                    f"Need {SEAT_COUNT}."
                )

                print(
                    "Skipping this class."
                )

                continue

            # ------------------------------------------------
            # BOOK NOW
            # ------------------------------------------------

            clicked = click_book_now(
                page,
                class_row
            )

            if not clicked:

                print(
                    "BOOK NOW failed."
                )

                continue

            print(
                "\nBOOK NOW clicked."
            )

            # ------------------------------------------------
            # CHECK EVERY COACH
            # ------------------------------------------------

            selected_seat_total = (
                check_all_coaches_in_class(
                    page,
                    SEAT_COUNT
                )
            )

            if (
                selected_seat_total
                >= SEAT_COUNT
            ):

                seat_selected = True

                print(
                    "\n================================================"
                )

                print(
                    "SUCCESS"
                )

                print(
                    "TRAIN:",
                    train_name
                )

                print(
                    "CLASS:",
                    class_name
                )

                print(
                    "TICKET AVAILABILITY:",
                    availability
                )

                print(
                    "SEATS REQUESTED:",
                    SEAT_COUNT
                )

                print(
                    "SEATS SELECTED:",
                    selected_seat_total
                )

                print(
                    "Stopping automation."
                )

                print(
                    "================================================"
                )

                break

            # ------------------------------------------------
            # NOT ENOUGH SEATS FOUND
            #
            # IMPORTANT:
            # Stay on seat selection page.
            # Do not go back.
            # Do not return to search results.
            # ------------------------------------------------

            print(
                "\n================================================"
            )

            print(
                "NOT ENOUGH AVAILABLE SEATS"
            )

            print(
                "================================================"
            )

            print(
                f"Requested: {SEAT_COUNT}"
            )

            print(
                f"Selected: {selected_seat_total}"
            )

            print(
                "Remaining on seat selection page."
            )

            print(
                "Stopping automation."
            )

            break

        # ----------------------------------------------------
        # STOP IF REQUIRED SEATS SELECTED
        # ----------------------------------------------------

        if seat_selected:

            break

        # ----------------------------------------------------
        # STOP AFTER ENTERING SEAT PAGE
        # ----------------------------------------------------

        if page.locator(
            ".seat-layout-view:visible"
        ).count() > 0:

            print(
                "\nSeat selection page is still open."
            )

            print(
                "Automation stopped here."
            )

            break

    # ========================================================
    # FINAL RESULT
    # ========================================================

    if not seat_selected:

        print(
            "\n================================================"
        )

        print(
            "AUTOMATION STOPPED"
        )

        print(
            f"Requested seats: {SEAT_COUNT}"
        )

        print(
            f"Selected seats: {selected_seat_total}"
        )

        print(
            "Browser remains on the current page."
        )

        print(
            "================================================"
        )

    else:

        print(
            "\nSeat selection complete."
        )

        print(
            f"{selected_seat_total} seat(s) selected."
        )

    # ========================================================
    # KEEP BROWSER OPEN
    # ========================================================

    input(
        "\nPress Enter when you want "
        "to close the browser..."
    )

    browser.close()