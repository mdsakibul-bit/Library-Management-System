LIBRARYDESK — LIBRARY MANAGEMENT SYSTEM WEBSITE
================================================

চালানোর সহজ নিয়ম (Windows):
1. ZIP ফাইল Extract All করুন।
2. Extract করা ফোল্ডার খুলুন।
3. run.bat ফাইলে ডাবল-ক্লিক করুন।
4. প্রথমবার Flask ইনস্টল করতে ইন্টারনেট লাগতে পারে।
5. ব্রাউজারে http://127.0.0.1:5000 খুলবে।

গুরুত্বপূর্ণ:
- এই প্রজেক্ট Flask + Python + SQLite ব্যবহার করে।
- এটি VS Code Live Server দিয়ে সরাসরি চালানো যায় না, কারণ Live Server Python/Flask backend চালায় না।
- run.bat ব্যবহার করাই সবচেয়ে সহজ। চাইলে VS Code Terminal-এ:
    python -m pip install -r requirements.txt
    python app.py
  তারপর ব্রাউজারে http://127.0.0.1:5000 খুলুন।
- Website বন্ধ করতে run.bat-এর কালো Terminal window-তে Ctrl+C চাপুন।
- ডেটা library.db ফাইলে সংরক্ষিত হয়। ফাইলটি মুছে ফেললে ডেটা হারিয়ে যাবে।
- এটি শিক্ষামূলক local demo; public hosting করার আগে security configuration উন্নত করতে হবে।
