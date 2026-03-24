**Live Demo (Frontend, 6-8 min)**

1. Start backend
    conda activate SplitRight
    cd /home/yash/Documents/VsCode Projects/SplitRight/backend
    python manage.py runserver

2. Open the app
- Go to http://127.0.0.1:8000/
- This is the integration console in index.html

3. Create 3 users
- Use Signup form for:
  - Alice, alice.demo@example.com, Password123!
  - Bob, bob.demo@example.com, Password123!
  - Carol, carol.demo@example.com, Password123!

4. Create one group (Alice session)
- Login as Alice
- Create Group: Trip Demo
- Note group_id from group selector / JSON output

5. Join same group with Bob and Carol
- Open 2 incognito windows (or 2 different browsers)
- Login as Bob, then Join Group using group_id
- Login as Carol, then Join Group using group_id

6. Show member list = 3 users
- Back in Alice window, click Refresh Groups
- Select Trip Demo in Group Selector
- Members box should show Alice, Bob, Carol

7. Add one expense tagging involved users
- In Add Expense:
  - paid_by: Alice user_id
  - amount: 300.00
  - split_type: equal
  - split_user_ids: alice_id,bob_id,carol_id
  - description: Hotel
- Submit
- Click Load Balances and Load Pairwise

Expected talking point:
- Alice paid 300, each share is 100
- Alice should get back 200
- Bob owes 100
- Carol owes 100

8. Record settlement
- In Settlements:
  - from_user: Bob
  - to_user: Alice
  - amount: 60.00
  - today’s date
- Submit
- Reload balances/pairwise

Expected talking point:
- Bob now owes only 40
- Carol still owes 100
- Alice net receivable becomes 140

9. Close with evidence
- Show:
  - Expenses panel
  - Balances panel
  - Pairwise panel
  - Settlements panel
- Mention backend tests passed (39 tests)

---
