Getting Started with lcu-driver
===============================

Basics
^^^^^^

An instance of Connector is responsible for holding both event handlers and create connections.

The connection instances will fire two events, **ready** and **close** and you can handle those using the decorators it provides.

.. literalinclude:: ../examples/tutorial/lcu_events.py
    :language: python


HTTP Requests
^^^^^^^^^^^^^
To easily make requests each connection provides a method wrapper around `aiohttp.Request <https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.request>`_ that allow us to make request without dealing with authentication or the port where it is running.


If you don't know where to find the Client APIs documentation checkout out `Rift Explorer <https://github.com/Pupix/rift-explorer>`_.

.. literalinclude:: ../examples/tutorial/http_request.py
    :language: python

You can find more about the method :meth:`here <lcu_driver.connection.Connection.request>`.

Websocket
^^^^^^^^^

.. literalinclude:: ../examples/tutorial/websocket.py
    :language: python

If you close the client you may notice it will not stop running. That happens because by default, if you subscribed to any endpoint, it will look for new clients once it's done.

To stop the connector once you disconnect runs all connection tasks you can use

.. code-block:: python

    @connector.close
    def disconnect(connection):
        print('The client was closed')
        await connector.stop()


URL Patterns
++++++++++++

What if you wanted to subscribe to all summoner events? You can simple register `/lol-summoner/` and since it ends with a trailing slash it will match every event url starting with it.

Examples
--------

**Not ending with trailing slash**
...................................
`@connector.ws.register('/lol-summoner')` will only match `/lol-summoner` and will never be fired because the endpoint doesn't exit.

**Ending with trailing slash**
..............................
`@connector.ws.register('/lol-summoner/')` will match every event starting with it.

It will match:
`/lol-summoner/v1/current-summoner`,
`/lol-summoner/v1/current-summoner/icon` and
`/lol-summoner/v1/summoners`

But not:
`/lol-perks/v1/pages`


