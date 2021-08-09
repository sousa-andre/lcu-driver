# lcu-driver

lcu-driver is a library made to communicate with League of Legends Client API in a easy way. It provides an API capable of handling LCU connection status and websockets events for you and prepare HTTP requests to be used directly with endpoints. Inspired in [lcu-connector](https://github.com/Pupix/lcu-connector). It has been tested on Windows, Linux and MacOS.

If you don't feel like using lcu-driver or it doesn't suit your needs, I recommend trying [Willump](https://github.com/elliejs/Willump). Willump is an amazing and simple alternative to this library.

<p>
    <a href="">
        <img src="https://img.shields.io/pypi/v/lcu-driver?style=for-the-badge" alt="PyPi">
    </a>
    <a href="">
        <img src="https://img.shields.io/github/last-commit/sousa-andre/lcu-driver?style=for-the-badge" alt="last-commit">
    </a>
    <a href="">
        <img src="https://img.shields.io/github/license/sousa-andre/lcu-driver?style=for-the-badge" alt="license">
    </a>
</p>

##### If you have any questions about how LCU API works or you're having problems with lcu-driver join [Riot API Dev Community](https://discord.gg/riotgamesdevrel) Discord server or send a private message to André#5360


## Download
 - `$ pip install lcu-driver`

### Problems
When running an application built using lcu-driver, some users will come across the **AccessDenied** error. To fix this error you should install psutil in a version earlier than 5.7.0. 

Running the command below should solve the problem.
 - `$ pip install -U psutil==5.6.5`


## Documentation
You can find lcu-driver documentation [here](https://lcu-driver.readthedocs.io/)

## Endorsement
lcu-driver isn’t endorsed by Riot Games and doesn’t reflect the views or opinions of Riot Games or anyone officially involved in producing or managing League of Legends. League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc. League of Legends © Riot Games, Inc.
