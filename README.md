Updated Live Demo Script (New Frontend, 6-8 min)

1. Start backend in SplitRight
- Terminal 1:
  conda activate SplitRight
  cd /home/yash/Documents/VsCode Projects/SplitRight/backend
  python manage.py migrate
  python manage.py runserver

2. Start frontend
- Terminal 2:Updated Live Demo Script (New Frontend, 6-8 min)

1. Start backend in SplitRight
- Terminal 1:
  conda activate SplitRight
  cd /home/yash/Documents/VsCode Projects/SplitRight/backend
  python manage.py migrate
  python manage.py runserver

2. Start frontend
- Terminal 2:
  conda activate SplitRight
  cd /home/yash/Documents/VsCode Projects/SplitRight/frontend
  npm install
  npm run dev

3. Open app
- Open: http://127.0.0.1:5173
- This is the new React UI (not the old JSON console).

4. Create 3 users
- On Login page, use Create Account for:
  - Alice, alice.demo@example.com, Password123!
  - Bob, bob.demo@example.com, Password123!
  - Carol, carol.demo@example.com, Password123!

5. Create group as Alice
- Login as Alice.
- Go to Groups page.
- Create Group: Trip Demo.
- Keep it joinable/discoverable enabled.

6. Join group as Bob and Carol (searchable dropdown)
- Open 2 incognito windows (or two other browsers).
- Login as Bob in one, Carol in the other.
- Go to Groups page.
- In Join Group, search Trip Demo from dropdown and join.
- No group ID entry needed.

7. Verify members = 3
- Back in Alice window, go to Groups page and refresh.
- Select Trip Demo as current group (top group dropdown or group card).
- Members table should show Alice, Bob, Carol.

8. Add one expense (no user IDs)
- Go to Expenses page (Alice window, current group Trip Demo).
- Fill:
  - Amount: 300.00
  - Date: today
  - Split Type: Equal
  - Description: Hotel
  - Payer dropdown: Alice
  - Split Members dropdown: Alice, Bob, Carol
- Submit.

9. Show balances and pairwise
- Go to Balances page.
- Click Load Group Balances.
- Click Load Pairwise Owes.
- Expected talking point:
  - Alice paid 300, each share 100
  - Alice net +200
  - Bob net -100
  - Carol net -100
  - Pairwise should show Bob -> Alice 100 and Carol -> Alice 100

10. Record settlement
- Go to Settlements page.
- Fill:
  - From User: Bob
  - To User: Alice
  - Amount: 60.00
  - Date: today
- Submit.
- Return to Balances page and reload Group Balances + Pairwise.

11. Final expected talking point
- Bob now owes 40
- Carol still owes 100
- Alice net receivable becomes 140

12. Close with evidence
- Show these screens:
  - Expenses tableUpdated Live Demo Script (New Frontend, 6-8 min)

1. Start backend in SplitRight
- Terminal 1:
  conda activate SplitRight
  cd /home/yash/Documents/VsCode Projects/SplitRight/backend
  python manage.py migrate
  python manage.py runserver

2. Start frontend
- Terminal 2:
  conda activate SplitRight
  cd /home/yash/Documents/VsCode Projects/SplitRight/frontend
  npm install
  npm run dev

3. Open app
- Open: http://127.0.0.1:5173
- This is the new React UI (not the old JSON console).

4. Create 3 users
- On Login page, use Create Account for:
  - Alice, alice.demo@example.com, Password123!
  - Bob, bob.demo@example.com, Password123!
  - Carol, carol.demo@example.com, Password123!

5. Create group as Alice
- Login as Alice.
- Go to Groups page.
- Create Group: Trip Demo.
- Keep it joinable/discoverable enabled.

6. Join group as Bob and Carol (searchable dropdown)
- Open 2 incognito windows (or two other browsers).
- Login as Bob in one, Carol in the other.
- Go to Groups page.
- In Join Group, search Trip Demo from dropdown and join.
- No group ID entry needed.

7. Verify members = 3
- Back in Alice window, go to Groups page and refresh.
- Select Trip Demo as current group (top group dropdown or group card).
- Members table should show Alice, Bob, Carol.

8. Add one expense (no user IDs)
- Go to Expenses page (Alice window, current group Trip Demo).
- Fill:
  - Amount: 300.00
  - Date: today
  - Split Type: Equal
  - Description: Hotel
  - Payer dropdown: Alice
  - Split Members dropdown: Alice, Bob, Carol
- Submit.

9. Show balances and pairwise
- Go to Balances page.
- Click Load Group Balances.
- Click Load Pairwise Owes.
- Expected talking point:
  - Alice paid 300, each share 100
  - Alice net +200
  - Bob net -100
  - Carol net -100
  - Pairwise should show Bob -> Alice 100 and Carol -> Alice 100

10. Record settlement
- Go to Settlements page.
- Fill:
  - From User: Bob
  - To User: Alice
  - Amount: 60.00
  - Date: today
- Submit.
- Return to Balances page and reload Group Balances + Pairwise.

11. Final expected talking point
- Bob now owes 40
- Carol still owes 100
- Alice net receivable becomes 140

12. Close with evidence
- Show these screens:
  - Expenses table
  - Group Balances table
  - Pairwise Owes table
  - Settlements history table
- Mention: backend checks passed and test suite passes in SplitRight (45 tests).

Important note
- Old endpoint http://127.0.0.1:8000 still serves the legacy integration console.
- New presentable frontend demo is on http://127.0.0.1:5173.

If you want, I can also give you a short presenter script (exact 60-90 second narration) to speak while clicking through.
  - Group Balances table
  - Pairwise Owes table
  - Settlements history table
- Mention: backend checks passed and test suite passes in SplitRight (45 tests).

Important note
- Old endpoint http://127.0.0.1:8000 still serves the legacy integration console.
- New presentable frontend demo is on http://127.0.0.1:5173.

If you want, I can also give you a short presenter script (exact 60-90 second narration) to speak while clicking through.
  conda activate SplitRight
  cd /home/yash/Documents/VsCode Projects/SplitRight/frontend
  npm install
  npm run dev

3. Open app
- Open: http://127.0.0.1:5173
- This is the new React UI (not the old JSON console).

4. Create 3 users
- On Login page, use Create Account for:
  - Alice, alice.demo@example.com, Password123!
  - Bob, bob.demo@example.com, Password123!
  - Carol, carol.demo@example.com, Password123!

5. Create group as Alice
- Login as Alice.
- Go to Groups page.
- Create Group: Trip Demo.
- Keep it joinable/discoverable enabled.

6. Join group as Bob and Carol (searchable dropdown)
- Open 2 incognito windows (or two other browsers).
- Login as Bob in one, Carol in the other.
- Go to Groups page.
- In Join Group, search Trip Demo from dropdown and join.
- No group ID entry needed.

7. Verify members = 3
- Back in Alice window, go to Groups page and refresh.
- Select Trip Demo as current group (top group dropdown or group card).
- Members table should show Alice, Bob, Carol.

8. Add one expense (no user IDs)
- Go to Expenses page (Alice window, current group Trip Demo).
- Fill:
  - Amount: 300.00
  - Date: today
  - Split Type: Equal
  - Description: Hotel
  - Payer dropdown: Alice
  - Split Members dropdown: Alice, Bob, Carol
- Submit.

9. Show balances and pairwise
- Go to Balances page.
- Click Load Group Balances.
- Click Load Pairwise Owes.
- Expected talking point:
  - Alice paid 300, each share 100
  - Alice net +200
  - Bob net -100
  - Carol net -100
  - Pairwise should show Bob -> Alice 100 and Carol -> Alice 100

10. Record settlement
- Go to Settlements page.
- Fill:
  - From User: Bob
  - To User: Alice
  - Amount: 60.00
  - Date: today
- Submit.
- Return to Balances page and reload Group Balances + Pairwise.

11. Final expected talking point
- Bob now owes 40
- Carol still owes 100
- Alice net receivable becomes 140

12. Close with evidence
- Show these screens:
  - Expenses table
  - Group Balances table
  - Pairwise Owes table
  - Settlements history table
- Mention: backend checks passed and test suite passes in SplitRight (45 tests).

Important note
- Old endpoint http://127.0.0.1:8000 still serves the legacy integration console.
- New presentable frontend demo is on http://127.0.0.1:5173.

If you want, I can also give you a short presenter script (exact 60-90 second narration) to speak while clicking through.