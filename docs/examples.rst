Code Examples
=============

Change summoner icon
*********************
Every time you run the code, if the summoner is logged in the client, it will change the current summoner icon for a random chinese icon (ids 50 to 78).

.. literalinclude:: ../examples/icons.py
    :language: python


Listening for summoner profile updates
**************************************
Once you run the code, the event handler (coroutine function) every time something about the summoner changes (e.g. name change, profile icon change, level, ...). The connection will keep alive until the client is closed.

.. literalinclude:: ../examples/summoner_change.py
    :language: python
