This is s snap-shot taken as

jochen@bruno:~/tmp_web_responsive$ git clone --no-checkout https://github.com/OCA/web.git
Cloning into 'web'...
remote: Enumerating objects: 95254, done.
remote: Counting objects: 100% (871/871), done.
remote: Compressing objects: 100% (452/452), done.
remote: Total 95254 (delta 696), reused 431 (delta 418), pack-reused 94383 (from 3)
Receiving objects: 100% (95254/95254), 221.59 MiB | 6.26 MiB/s, done.
Resolving deltas: 100% (43999/43999), done.
jochen@bruno:~/tmp_web_responsive$ cd web
jochen@bruno:~/tmp_web_responsive/web$ git sparse-checkout init --cone
git sparse-checkout set web_responsive
jochen@bruno:~/tmp_web_responsive/web$ git checkout 5ebe075522220d52196e6bd5f3b1eb9d57250089
Note: switching to '5ebe075522220d52196e6bd5f3b1eb9d57250089'.

HEAD is now at 5ebe07552 [FIX] web_responsive: change code to be compatible upstream

see https://github.com/OCA/web/commit/5ebe075522220d52196e6bd5f3b1eb9d57250089
for the latest change that we will need to reverse out for the time being
