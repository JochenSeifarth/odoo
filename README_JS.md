# Odoo

jochen@bruno:~$ cd git
jochen@bruno:~/git$ cd odoo/
jochen@bruno:~/git/odoo$ python3 -m venv venv_odoo
jochen@bruno:~/git/odoo$ source venv_odoo/bin/activate
(venv_odoo) jochen@bruno:~/git/odoo$ pip install -r requirements.txt

### Git
# 19.0 in meinem repo ist quasi master

git checkout 19.0

# 2️⃣ Upstream hinzufügen (nur einmal nötig)
git remote add upstream https://github.com/odoo/odoo.git

# 3️⃣ Neueste Änderungen von upstream holen
git fetch upstream

# 4️⃣ Rebase deines Branches auf upstream/19.0
git rebase upstream/19.0

# 5️⃣ Änderungen zu deinem Fork pushen
git push origin 19.0