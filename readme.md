# Personal Banking System

> A desktop banking application built in Python featuring a relational SQL database, AI-powered banking assistant, user authentication, transactions, scheduled payments, and account management.

> **Status:** Work in Progress  
> **Language:** Python  
> **Database:** SQL  
> **AI:** Gemini 3.1 Flash Lite  
> **GUI:** Tkinter / CustomTkinter + Threading

---

## Why This Project?

This is my second Python project.

I probably should have picked something smaller.

Instead, I decided to build an entire banking system with a SQL database, user authentication, account management, bank cards, transactions, scheduled payments, an AI assistant, and a desktop GUI.

Looking back, it was probably a bit too ambitious... but I'm glad I went for it. It forced me to work on databases, authentication, AI integration, desktop development, and plenty of debugging along the way. Best of all, I had a lot of fun doing it.

The project is still a work in progress, but it's reached the point where I'm happy to put it on GitHub and let other people see what I've built.

---

## Screenshots

 --> Check the screenshots folder

---

## Technologies

- Python
- SQL
- Gemini 3.1 Flash Lite
- Tkinter / CustomTkinter
- Threading
- JSON

---

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` |  |
| `GUI.py` | Handles the desktop interface. |
| `DBsys.py` | Backend logic and database communication. |
| `ai.py` | AI assistant and market information retrieval. |
| `banking_system_schema.sql` | SQL database schema. |
| `commodities.json` | Local commodity cache used as a fallback. |

Keeping everything separated made debugging much easier. If something breaks, I usually already know roughly where to start looking instead of digging through thousands of lines in one file.

---

> ### Project Stats
>
> - **Language:** Python
> - **Database:** SQL
> - **AI:** Gemini 3.1 Flash Lite
> - **GUI:** Tkinter / CustomTkinter
>
> - ~8,000+ lines of Python
> - 15+ SQL tables
> - 40+ database methods

---

## Database

Everything revolves around the SQL database (banking_system_schema.sql).
It currently contains:
	•	Users
	•	User security (password hashing + salt)
	•	Accounts
	•	Cards
	•	MB Way links (Portuguese users will know exactly what this is)
	•	Transactions
	•	Payment codes
	•	Scheduled / recurring payments
	•	Market assets
	•	Audit logs
	•	Sessions
	•	Database views for account overviews and upcoming payments
At some point I'll probably make an ER diagram.
Mostly because future me is eventually going to open this project again and wonder what past me was thinking.

---

## Backend (`DBsys.py`)

If this project has a brain, this is it.
DBsys.py is responsible for almost every interaction with the database.
Creating users, logging users in, creating accounts and cards, making transactions, executing SQL queries, updating records and deleting records.
Pretty much every database operation goes through this file.
It ended up becoming much larger than I originally planned, but separating the backend from the GUI made everything much easier to organise and debug.


---

## AI (`ai.py`)

Originally, I wanted the AI to scrape financial websites for live commodity and currency prices.
Then I learned about robots.txt, Terms of Service, and that "because something works" isn't always the same as "because you should".
So I changed direction.
Instead of pretending to be Bloomberg, the AI acts more like a virtual bank employee. It can answer questions about accounts, explain banking features, help users understand their finances, and discuss assets such as gold using locally stored market information.
It runs on Gemini 3.1 Flash Lite, which turned out to be more than enough for what I needed without burning through API costs.
The AI also uses a local commodities.json file containing commodity and currency data. Every update is timestamped so the assistant knows how recent the information is.
One feature I'm particularly happy with is the fallback system.
Whenever the AI tries to retrieve fresh market information, it has an 8-second timeout. If it can't get the information in time, it doesn't simply fail or leave the user waiting forever. Instead, it automatically falls back to the locally stored data in commodities.json.
More importantly, it tells the user exactly what's happening.
Rather than pretending the information is live, the AI explains that the response comes from the bank's saved data and recommends treating it as a reference rather than absolute truth. Basically:
"Here's the best information I currently have, but if you're making an important financial decision, it's worth double checking a live source."
I liked that approach a lot more than simply throwing an error.


---

## GUI

The database was fun, the backend was fun, even integrating the AI was surprisingly enjoyable, but the GUI...
The GUI fought me every single step of the way.
I have a lot more respect for frontend developers now because making something look simple is anything but simple.
I did get some help from Claude Code while building parts of the interface, but all of the backend logic, database integration and AI functionality is my own work.
The application currently allows users to:
	•	Log in
	•	Register a new account
	•	Contact the bank if they're having login issues
	•	View account information
	•	Create accounts
	•	Request bank cards
	•	Make transactions
	•	Generate payment codes
	•	Schedule payments
	•	Chat with the AI assistant
...and there's still more I'd like to add.


---

## Things That Still Need Fixing

The project isn't finished, and I'm not going to pretend it is.
Some of the current issues include:
- [ ] Session information can carry over.
- [ ] Login fields sometimes retain previous data.
- [ ] AI chat wrapping still needs work.

They're all on the list.
Just... maybe after I enjoy what's left of my summer vacation.

---

## What I Learned

One thing this project taught me is that software grows much faster than you think.
I started with what sounded like a fairly simple idea: "Let's build a banking system" then one feature became two, two became ten and before I knew it I was juggling a database, authentication, sessions, a desktop GUI, an AI assistant, JSON files, and trying to make all of them work together without breaking anything else.
There are plenty of things I'd do differently if I started again today, and there are definitely parts of the code that make me stop and think, "What exactly was I trying to do here?", but I think that's part of learning.
If I look back at this project in five years and still think every decision I made was perfect, then I probably haven't improved much.

---

## If I Started Again Today

If I Started Again Today I'd probably change a few things: 
- Split DBsys.py into smaller modules instead of one large backend file. 
- Add automated tests much earlier instead of relying mostly on manual testing. 
- Design the GUI around reusable components from the start instead of adding them as the project grew.


---

## If I Started Again Today

- Split `DBsys.py` into smaller modules.
- Add automated testing earlier.
- Design reusable GUI components from the beginning.

---

## Final Thoughts

I'm currently a Computer Science student going into my third year, with most of my experience coming from C, Java, Haskell, SQL, Algorithms, OOP, functional and imperative programming, Logic, Applied Probability and algebra.
This project was my way of seeing how much I could build by bringing everything I knew together into a single application.
It's not trying to simulate a real bank perfectly, and it's definitely not finished. There are features I'd like to add, bugs I'd like to fix, and probably quite a few questionable design decisions that future me will eventually rewrite.
But that's kind of the point.
This repository isn't here because it's perfect. It's here because it shows where I am right now as a developer, and I think that'll be much more interesting to look back on in a few years than if I waited until everything was "finished."


---

## Contributing

If you spot something I could improve, find a bug, or simply want to talk about the project, feel free to open an issue or a pull request.

I'd genuinely like to hear how other people would have approached the same problems.
