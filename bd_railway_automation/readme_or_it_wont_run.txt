HOW TO SET UP THE ZIP FILE AND VIRTUAL ENVIRONMENT IN YOUR PC?

The PC must have:
* Python installed
* Google Chrome installed
* VS Code installed
* Internet connection

1. EXTRACT THE PROJECT
Extract the ZIP file anywhere you want.

2. OPEN THE PROJECT IN VS CODE
Open VS Code.
File > Open Folder
Select the extracted project folder.

3. CREATE A VIRTUAL ENVIRONMENT
Open the VS Code terminal. then Run:

python -m venv venv

4. ACTIVATE THE VIRTUAL ENVIRONMENT
Run :
venv\Scripts\Activate.ps1

If PowerShell blocks the command, use:
venv\Scripts\activate.bat

5. INSTALL PLAYWRIGHT
Run:
pip install playwright

6. NOW CHECK THE NEW PROJECT FILES AUTO CREATED
The project contained:
main.py
start.bat
readme_or_it_wont_run.txt

The following folders are created automatically later on:
venv
chrome-profile
**pycache**

7. RUN THE AUTOMATION
Double-click:
start.bat
Chrome will open with a separate browser profile. stay signed out.
The Railway website will open automatically.

8. FIRST TIME LOGIN
If Railway asks you to log in:
- Log in manually in the Chrome window.
- Complete any CAPTCHA if required.
- Wait.
The Python script will detect the login and continue automatically. 


9. Change Route and Date
Open main.py(line 7):
At the top, change these settings:
FROM_CITY = "Dhaka"
TO_CITY = "Rajshahi"
YEAR = 2026
MONTH = 9
DAY = 24
The station names should match the suggestions shown by the railway website. careful with spelling.

10 . What the Automation Does?
-Opens the railway website.
-Accepts the disclaimer automatically if it appears.
-Waits for manual login if login is required.
-Selects the departure station.
-Selects the destination station.
-Selects the journey date.
-Searches for trains.
-Opens each available train.
-Checks all available classes.
-Checks the available ticket count.
-Clicks BOOK NOW for a class with available tickets.
-Searches the seat layout.
-Finds an available seat.
-Selects the seat.

If no train has any available tickets, it shows:
NO SEATS LEFT FOR THIS ROUTE

11. IMPORTANT:
The automation does not complete the payment automatically.
After seat selection, continue the remaining booking and payment process manually.
If CAPTCHA, OTP, or any verification appears, complete it manually.
!!! THIS AUTOMATION BROWSER IS NOT TESTED YET WITH BKASH NAGAD OR ANY PAYMENTGATEWAYS.!!!!