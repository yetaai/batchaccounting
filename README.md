Batch accounting by importing .OFX and .QFX files
==============================================
** Smells not good? It is 21 century, we shall have auto connection with banks, right? **

But data are toys of big players who will not let you automate it. They will earn
money use your time and effort. Not a secret.

Batch accounting is the best tool for individuals now. It supports importing ``OFX`` and
``QFX`` for major banks and financial institutions. On this basis, the accounting software
is designed and implemented.

QFX is a variant of OFX actually in my opinion. I am not sure that big player has patent or
trademark on it. But there are lot of pain points for individuals using it.

* Some major banks only supports QFX but not OFX.
* QFX has many fabulous tricks to make OFX parsers not function well even not work. Or even
worse, working wrongfully without any error message. Terrible!!
* CSV file often does not contain necessary meta information enough for account consolidation.

So a refined OFX parser and consolidating management featured accouting software is quite
necessary.

So here is the list of features:

* By importing .OFX/.QFX file, financial organization and account master skelete are automatically
 created.
* Auto and intelligent reconciliation.
* Raw transactions and double book journals are separately stored.
* You can re-do journal at any time from scratch.
* Accounts receivable/payable aging report is almost no work.
* Simple command line
* Mysql with simple tables.

Thanks ofx protocols and python and ofxtools contibutors.